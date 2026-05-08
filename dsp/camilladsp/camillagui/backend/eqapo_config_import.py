import logging
from copy import copy


class EqAPO:
    filter_types = {
        "PK": "Peaking",
        "PEQ": "Peaking",
        "HP": "Highpass",
        "HPQ": "Highpass",
        "LP": "Lowpass",
        "LPQ": "Lowpass",
        "BP": "Bandpass",
        "NO": "Notch",
        "LS": "Lowshelf",
        "LSC": "Lowshelf",
        "HS": "Highshelf",
        "HSC": "Highshelf",
        "IIR": None,  # TODO
    }
    # TODO
    # add support for
    # HSC x dB: High-shelf filter x dB per oct.
    # LSC x dB: Low-shelf filter x dB per oct.
    # LS 6dB: Low-shelf filter 6 dB per octave, with corner freq.
    # LS 12dB: Low-shelf filter 12 dB per octave, with corner freq.
    # HS 6dB: High-shelf filter 6 dB per octave, with corner freq.
    # HS 12dB: High-shelf filter 12 dB per octave, with corner freq.

    # Label to channel number
    all_channel_maps = {
        1: {"C": 1},
        2: {"L": 0, "R": 1},
        4: {"L": 0, "R": 1, "RL": 2, "RR": 3},
        6: {"L": 0, "R": 1, "C": 2, "LFE": 3, "RL": 4, "RR": 5},
        8: {"L": 0, "R": 1, "C": 2, "LFE": 3, "RL": 4, "RR": 5, "SL": 6, "SR": 7},
    }

    delay_units = {"ms": "ms", "samples": "samples"}

    def __init__(self, config_text, nbr_channels):
        self.lines = config_text.splitlines()
        self.filters = {}
        self.mixers = {}
        self.name_index = {
            "Filter": 1,
            "Preamp": 1,
            "Convolution": 1,
            "Delay": 1,
            "Copy": 1,
        }
        self.selected_channels = None
        self.current_filterstep = {
            "type": "Filter",
            "names": [],
            "description": "Default, all channels",
            "channels": copy(self.selected_channels),
        }
        self.pipeline = [self.current_filterstep]
        self.nbr_channels = nbr_channels
        self.channel_map = self.all_channel_maps.get(
            nbr_channels, self.all_channel_maps[8]
        )

    def lookup_channel_index(self, label):
        if label in self.channel_map:
            channel = self.channel_map[label]
        elif label.isnumeric():
            channel = int(label) - 1
        else:
            logging.warning(
                "Virtual channels are not supported, skipping channel %s", label
            )
            channel = None
        return channel

    def parse_number(self, value_str):
        try:
            return float(value_str)
        except ValueError:
            logging.warning(
                "Unable to parse '%s' as number, inline expressions are not supported.",
                value_str,
            )
            return None

    # Parse a single command parameter
    def parse_single_parameter(self, params):
        # Inline expressions (ex: Fc `2*a`) are not supported
        # TODO add a check for this.
        if params[0] == "Fc":
            nbr_tokens = 3
            assert params[2].lower() == "hz"
            value = self.parse_number(params[1])
            parsed = {"freq": value}
        elif params[0] == "Q":
            nbr_tokens = 2
            value = self.parse_number(params[1])
            parsed = {"q": value}
        elif params[0] == "Gain":
            nbr_tokens = 3
            assert params[2].lower() == "db"
            value = self.parse_number(params[1])
            parsed = {"gain": value}
        elif params[0] == "BW":
            nbr_tokens = 3
            assert params[1].lower() == "oct"
            value = self.parse_number(params[2])
            parsed = {"bandwidth": value}
        else:
            logging.warning("Skipping unknown token: %s", params[0])
            return {}, params[1:]
        return parsed, params[nbr_tokens:]

    # Parse the parameters for a command
    def parse_filter_params(self, param_str):
        params = param_str.split()
        # TODO skip this command if OFF
        # enabled = params[0] == "ON"
        ftype = params[1]
        ftype_c = self.filter_types.get(ftype)
        if not ftype_c:
            logging.warning("Unsupported filter type '%s'", ftype)
            return None
        param_dict = {"type": ftype_c}
        tokens = params[2:]
        while tokens:
            p, tokens = self.parse_single_parameter(tokens)
            param_dict.update(p)
        return param_dict

    # Parse a Preamp command to a filter
    def parse_gain(self, param_str):
        params = param_str.split()
        gain = self.parse_number(params[0])
        if params[1].lower() != "db":
            logging.warning("invalid preamp line: %s", param_str)
            return None
        return {"type": "Gain", "parameters": {"gain": gain, "scale": "dB"}}

    # Parse a Delay command to a filter
    def parse_delay(self, param_str):
        params = param_str.split()
        delay = self.parse_number(params[0])
        unit = self.delay_units[params[1]]
        return {"type": "Delay", "parameters": {"delay": delay, "unit": unit}}

    # Parse a Copy command into a Mixer
    def parse_copy(self, param_str):
        handled_channels = set()
        mixer = {
            "channels": {
                "in": self.nbr_channels,
                "out": self.nbr_channels,
            },
            "mapping": [],
        }
        params = param_str.strip().split(" ")
        for dest in params:
            dest_ch, expr = dest.split("=")
            dest_ch = self.lookup_channel_index(dest_ch)
            handled_channels.add(dest_ch)
            logging.debug("dest %s", dest_ch)
            mapping = {"dest": dest_ch, "mute": False, "sources": []}
            mixer["mapping"].append(mapping)
            sources = expr.split("+")
            for source in sources:
                if "*" in source:
                    gain_str, channel = source.split("*")
                    if gain_str.endswith("dB"):
                        gain = self.parse_number(gain_str[:-2])
                        scale = "dB"
                    else:
                        gain = self.parse_number(gain_str)
                        scale = "linear"
                elif source == "0.0":
                    # EqAPO supports setting channels to an arbitrary constant.
                    # Here only 0.0 is supported, as other values have no practical use.
                    channel = None
                    scale = None
                    gain = None
                else:
                    gain = 0
                    scale = "dB"
                    channel = source
                if channel is not None:
                    channel = self.lookup_channel_index(channel)
                    # TODO make a mixer config
                    logging.debug(
                        "source channel: %s, gain: %f, scale: %s", channel, gain, scale
                    )
                    source = {
                        "channel": channel,
                        "gain": gain,
                        "inverted": False,
                        "scale": scale,
                    }
                    mapping["sources"].append(source)
        for dest_ch in set(range(self.nbr_channels)) - handled_channels:
            logging.debug("pass through %s", dest_ch)
            mapping = {
                "dest": dest_ch,
                "mute": False,
                "sources": [
                    {
                        "channel": dest_ch,
                        "gain": 0.0,
                        "inverted": False,
                        "scale": "dB",
                    }
                ],
            }
            mixer["mapping"].append(mapping)
        return mixer

    # Parse a single line
    def parse_line(self, line):
        if not line or line.startswith("#") or not ":" in line:
            return
        filtname = None
        command_name, params = line.split(":", 1)
        command = command_name.split()[0]
        logging.debug("Parse command: %s", command)
        if command in ("Filter", "Convolution", "Preamp", "Delay"):
            filt = {}
            if command == "Filter":
                filterparams = self.parse_filter_params(params)
                if not filterparams:
                    return
                filt = {"type": "Biquad", "parameters": filterparams}
            elif command == "Convolution":
                filename = params.strip()
                filt = {
                    "type": "Conv",
                    "parameters": {"filename": filename, "type": "wav"},
                }
            elif command == "Preamp":
                filt = self.parse_gain(params)
            elif command == "Delay":
                filt = self.parse_delay(params)
            filt["description"] = line.strip()
            filtname = f"{command}_{self.name_index[command]}"
            self.name_index[command] += 1
            self.filters[filtname] = filt
            self.pipeline[-1]["names"].append(filtname)
        elif command == "Channel":
            if params.strip() == "all":
                self.selected_channels = None
            else:
                self.selected_channels = [
                    self.lookup_channel_index(c) for c in params.strip().split(" ")
                ]
            new_filterstep = {
                "type": "Filter",
                "names": [],
                "description": line.strip(),
                "channels": copy(self.selected_channels),
            }
            self.pipeline.append(new_filterstep)
        elif command == "Copy":
            mixer = self.parse_copy(params)
            mixer["description"] = line.strip()
            mixername = f"{command}_{self.name_index[command]}"
            self.name_index[command] += 1
            self.mixers[mixername] = mixer
            step = {
                "type": "Mixer",
                "name": mixername,
            }
            self.pipeline.append(step)
            step = {
                "type": "Filter",
                "names": [],
                "description": "Continued after mixer",
                "channels": copy(self.selected_channels),
            }
            self.pipeline.append(step)
        elif command in (
            "Device",
            "Include",
            "Eval",
            "If",
            "ElseIf",
            "Else",
            "EndIf",
            "Stage",
            "GraphicEQ",
        ):
            logging.warning("Command '%s' is not supported, skipping.", command)
        else:
            logging.warning("Skipping unrecognized command '%s'", command)

    def postprocess(self):
        for idx, step in enumerate(list(self.pipeline)):
            if step["type"] == "Filter" and len(step["names"]) == 0:
                logging.debug("remove %s", step)
                self.pipeline.remove(step)
        for _, mixer in self.mixers.items():
            for idx, dest in enumerate(list(mixer["mapping"])):
                if len(dest["sources"]) == 0:
                    mixer["mapping"].pop(idx)

    def build_config(self):
        config = {
            "filters": self.filters,
            "mixers": self.mixers,
            "pipeline": self.pipeline,
        }
        return config

    def translate_file(self):
        for line in self.lines:
            self.parse_line(line)
        self.postprocess()
        config = self.build_config()
        return config

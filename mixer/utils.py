import subprocess
import alsaaudio
import re

def aplay_devices():
    output = subprocess.check_output(["aplay", "-L"], text=True)
    cards = alsaaudio.cards()
    results = []
    lines = output.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith(" "):
            i += 1
            continue

        if line.startswith(("hw:", "plughw:")):
            device_name = line

            desc = ""
            if i + 1 < len(lines) and lines[i + 1].startswith(" "):
                desc = lines[i + 1].strip()

            match = re.search(r"CARD=([^,]+)", device_name)
            if not match:
                i += 1
                continue

            card_name = match.group(1)

            try:
                card_index = cards.index(card_name)
            except ValueError:
                card_index = None

            mixers = []
            if card_index is not None:
                try:
                    mixers = alsaaudio.mixers(cardindex=card_index)
                except alsaaudio.ALSAAudioError:
                    mixers = []

            results.append({
                "device": device_name,
                "description": desc,
                "card_name": card_name,
                "card_index": card_index,
                "mixer_controls": mixers
            })

        i += 1

    return results



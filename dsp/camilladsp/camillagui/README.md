# Backend server for CamillaGUI

This is the server part of CamillaGUI, a web-based GUI for CamillaDSP.

This version works with CamillaDSP 4.0.x.

The complete GUI is made up of two parts:
- a frontend based on React: https://reactjs.org/
- a backend based on AIOHTTP: https://docs.aiohttp.org/en/stable/

## Download a complete bundle
The easiest way to run the gui is to download and run one of the published bundles.
These contain the gui backend server, the frontend files,
and a complete Python environment.
Bundles are provided for most common systems and cpu architectures.

### Downloading the bundled gui
Go to "Releases": https://github.com/HEnquist/camillagui-backend/releases
Download the bundle for you system, for example "bundle_linux_amd64.tar.gz"
for a linux system running an AMD or Intel cpu.
Uncompress the archive to a directory of your choice.
A suggestion is to create a directory named `camilladsp`
in you home directory, and place the `camillagui_backend` in it.
Also create directories named `configs` and `coeffs` in the `camilladsp` directory.

### Configuring the bundled gui
The gui configuration is stored in the bundle,
at `camillagui_backend/_internal/config/camillagui.yml`.
See [Configuration](#configuration) for an explanation of the options.
The default confuguration uses the `configs` and `coeffs` directories
created in the previous step, but these locations can be changed by
editing the configuration file.

### Running the bundled gui
The archive contains a directory called `camillagui_backend`.
Inside this directory there is an executable named `camillagui_backend`
(or `camillagui_backend.exe` on windows).
Run this executable to start the gui backend.

## Setting up a in a Python environment
This option sets up the gui backend in a Python environment.
This gives more flexibility to customize the system,
for example to develop Python scrips that use the pycamilladsp library.

### Download the gui server
Go to "Releases": https://github.com/HEnquist/camillagui-backend/releases
Download the zip-file ("camillagui.zip") for the latest release. This includes both the backend and the frontend.

Unzip the file and edit `camillagui_backend/config/camillagui.yml` as needed, see [Configuration](#configuration).

### Python dependencies
The Python dependencies are listed in three different files,
for use with different Python package/environment managers.
- `cdsp_conda.yml` for [conda](https://conda.io/).
- `requirements.txt` for [pip](https://pip.pypa.io/), often combined with an environment manager
  such as [venv](https://docs.python.org/3/library/venv.html).
- `pyproject.toml` for [Poetry](https://python-poetry.org).


### Prepare the Python environment
The easiest way to get the Python environment prepared is to use the setup scripts from
[camilladsp-setupscripts](https://github.com/HEnquist/camilladsp-setupscripts).

If doing a manual installation, there are many ways of installing Python and setting up environments.
Please see the [documentation for pycamilladsp](https://henquist.github.io/pycamilladsp/install/#installing)
for more information.


## Configuration

The backend configuration is stored in `camillagui_backend/config/camillagui.yml` by default.
Note that in the [bundled executable](#configuring-the-bundled-gui),
it is instead located at `camillagui_backend/_internal/config/camillagui.yml`.

Example:
```yaml
---
camilla_host: "0.0.0.0"
camilla_port: 1234
bind_address: "0.0.0.0"
port: 5005
ssl_certificate: null (*)
ssl_private_key: null (*)
gui_config_file: null (*)
config_dir: "~/camilladsp/configs"
coeff_dir: "~/camilladsp/coeffs"
default_config: "~/camilladsp/default_config.yml"
statefile_path: "~/camilladsp/statefile.yml"
log_file: "~/camilladsp/camilladsp.log" (*, defaults to null)
on_set_active_config: null (*)
on_get_active_config: null (*)
supported_capture_types: null (*)
supported_playback_types: null (*)
```
The options marked `(*)` are optional. If left out the default values listed above will be used.
The included configuration has CamillaDSP running on the same machine as the backend,
with the websocket server enabled at port 1234.
The web interface will be served on port 5005 using plain HTTP.
It is possible to run the gui and CamillaDSP on different machines,
just point the `camilla_host` to the right address.

The optional `gui_config_file` can be used to override the default path to the gui config file.

**Warning**: By default the backend will bind to all network interfaces.
This makes the gui available on all networks the system is connected to, which may be insecure.
Make sure to change the `bind_address` if you want it to be reachable only on specific
network interface(s) and/or to set your firewall to block external (internet) access to this backend.

The `ssl_certificate` and `ssl_private_key` options are used to configure SSL, to enable HTTPS.
Both a certificate and a private key are required.
The values for `ssl_certificate` and `ssl_private_key` should then be
the paths to the files containing the certificate and key.
It's also possible to keep both certificate and key in a single file.
In that case, provide only `ssl_certificate`.
See the [Python ssl documentation](https://docs.python.org/3/library/ssl.html#ssl-certificates)
for more info on certificates.

To generate a self-signed certificate and key pair, use openssl:
```sh
openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -keyout my_private_key.key -out my_certificate.crt
```

The settings for config_dir and coeff_dir point to two folders where the backend has permissions to write files.
This is provided to enable uploading of coefficients and config files from the gui.

If you want to be able to view the log file in the GUI, configure CamillaDSP to log to `log_file`.

### Active config file
The active config file path is memorized via the CamillaDSP state file.
Set the `statefile_path` to point at the statefile that the CamillaDSP process uses.
For this to work, CamillaDSP must be running with a statefile.
That is achieved by starting it with the `-s` parameter,
giving the same path to the statefile as in `camillagui.yml`:
```sh
camilladsp -p 1234 -w -s /path/to/statefile.yml
```

If the CamillaDSP process is running, the active config file path
will be fetched by querying the running process.
If its not running, it will instead be read directly from the statefile.

The active config will be loaded into the web interface when it is opened.
If there is no active config, the `default_config` will be used.
If this does not exist, the internal default config is used.
Note: the active config will NOT be automatically applied to CamillaDSP, when the GUI starts.

See also [Integrating with other software](#integrating-with-other-software)


### Limit device types
By default, the config validator allows all the device types that CamillaDSP can support.
To limit this to the types that are supported on a particular system, give the list of supported types as:
```yaml
supported_capture_types: ["Alsa", "File", "Stdin"]
supported_playback_types: ["Alsa", "File", "Stdout"]
```

### Integrating with other software
If you want to integrate CamillaGUI with other software,
there are some options to customize the UI for your particular needs.

#### Setting and getting the active config
_NOTE: This functionality is experimental, there may be significant changes in future versions._

The configuration options `on_set_active_config` and `on_get_active_config` can be used to customize
the way the active config file path is stored.
These are shell commands that will be run to set and get the active config.
Setting these options will override the normal way of getting and setting the active config path.
Since the commands are run in the operating system shell, the syntax depends on which operating system is used.
The examples given below are for Linux.

The `on_set_active_config` uses Python string formatting to insert the filename.
This means it must contain an empty set of curly brackets, where the filename will get inserted surrounded by quotes.

Examples:
- Running a script: `on_set_active_config: my_updater_script.sh {}`

  The backend will run the command: `my_updater_script.sh "/full/path/to/new_active_config.yml"`
- Saving config filename to a text file: `on_set_active_config: echo {} > active_configname.txt`

  The backend will run the command: `echo "/full/path/to/new_active_config.yml" > active_configname.txt`

The `on_get_active_config` command is expected to return a filename on stdout.
As an example, read a filename from a text file: `on_get_active_config: "cat myconfig.txt"`.


## Customizing the GUI
Some functionality of the GUI can be customized by editing `camillagui_backend/config/gui-config.yml`.
The styling can be customized by editing `camillagui_backend/build/css-variables.css`.

### GUI title
Change the GUI title by setting `page_title`.
This helps distinguish multiple CamillaDSP instances on the network,
for example "Living room" and "Headphone system".
This will be shown as the page title in the browser,
making it easy to identify which GUI controls which setup.

### Volume control range
The range of the volume control slider can be customized by changing
the valkues of `volume_range` and `volume_max`.
The default values are a range of 50 dB and a maximum of 0 dB.

### Adding custom shortcut settings
It is possible to configure custom shortcuts for the `Shortcuts` section and the compact view.
The included config file contains the default Bass and Treble filters,
as well as a few commented out examples.

To add more, edit the file `camillagui_backend/config/gui-config.yml` to add
the new shortcuts to the list under `custom_shortcuts`.

Here is an example config to set the gain of the filters called `MyFilter` and `MyOtherFilter`.
within the range from -10 to 0 db in steps of 0.1 dB.
For `MyOtherFilter`, the scale is reversed, such that moving the slider from -10 to -9 dB
changes the gain of `MyOtherFilter` fom 0 to -1 dB.
The `type` property is set to `number`.
This creates a slider control, used to control numerical values.
It can also be set to `boolean` which creates a checkbox.
For `number`, the `range_from`, `range_to` and `step` properties are required.
They are not used by `boolean` controls and may be left out.

```yaml
custom_shortcuts:
  - section: "My custom section"
    description: |
      Optional description for the section.
      Omit this attribute, if unwanted.
      The text will be shown in the gui with line breaks.
    shortcuts:
      - name: "My filter gain"
        description: |
          Optional description for the setting.
          Omit this attribute, if unwanted.
        config_elements:
          - path: ["filters", "MyFilter", "parameters", "gain"]
            reverse: false
          - path: ["filters", "MyOtherFilter", "parameters", "gain"]
            reverse: true
        range_from: -10
        range_to: 0
        step: 0.1
        type: "number"
```
When letting a shortcut control more than one element in the config,
the first one is considered the main one, that controls the slider position.
The first element must be present in the config in order for the shortcut to function.

If any of the others is not at the expected value, the GUI will show a warning.
The same happens if any of the others is missing in the config.
The control can then still be used, but may not give the wanted result.

### Hiding GUI Options
Options can be hidden from your users by editing `camillagui_backend/config/gui-config.yml`.
Setting any of the options to `true` hides the corresponding option or section.
These are all optional, and default to `false` if left out.
```yaml
hide_capture_samplerate: false
hide_silence: false
hide_capture_device: false
hide_playback_device: false
hide_rate_monitoring: false
hide_multithreading: false
```

### Styling the GUI
The UI can be styled by editing `camillagui_backend/build/css-variables.css`.
Further instructions on how to do this, or switch back to the brighter black/white UI, can be found there.

### Other GUI Options
Changes to the currently edited config can be applied automatically, but this behavior is disabled by default.
To enable it by default, in `camillagui_backend/config/gui-config.yml` set `apply_config_automatically` to `true`.

The update rate of the level meters can be adjusted by changing the `status_update_interval` setting.
The value is in milliseconds, and the default value is 100 ms.

### Gui config syntax check
The gui config is checked when the backend starts, and any problems are logged.
For example, the `range_from` property of a config shortcut must be a number.
If it is not, this results in a message such as this:
```
ERROR:root:Parameter 'custom_shortcuts/0/shortcuts/1/range_from': 'hello' is not of type 'number'
```

## Running
If using the bundle, start the server by changing to the directory
containing the executable and run running it.
Linux and macOS:
```sh
./camillagui_backend
```
```sh
camillagui_backend.exe
```
On windows it is also possible to start by double-clicking the .exe-file.

For a Python environment, the command for starting the server is:
```sh
python main.py
```

All methods of starting the server accept the same command line arguments,
and running with `--help` shows the available arguments.

The gui should now be available at: http://localhost:5005/gui/index.html

If accessing the gui from a different machine, replace "localhost" by the IP
or hostname of the machine running the gui server.

### Command line options
The logging level for the backend itself as well as the AIOHTTP framework are set to `WARNING` by default.
These can both be changed with command line arguments, which may be useful when debugging some problem.

The backend norally reads its configuration from a default location.
This can be changed by providing a different path as a command line argument.

Use the `-h` or `--help` argument to view the built-in help:
```
> python main.py --help
usage: python main.py [-h] [-c CONFIG] [-l {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}]
                      [-a {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}]

Backend for the CamillaDSP web GUI

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Provide a path to a backend config file to use instead of the default
  -l {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}, --log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}
                        Logging level
  -a {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}, --aiohttp-log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}
                        AIOHTTP logging level
```


## Development
### Render the environment files
This repository contains [jinja](https://palletsprojects.com/p/jinja/)
templates used to create the Python environment files.
The templates are stored in `release_automation/templates/`.

To render the templates, install the dependencies `PyYAML` and `jinja2`
and run the Python script `render_env_files.py`:
```sh
python -m release_automation.render_env_files
```
When rendering, the versions of the Python dependencies are taken
from the file `release_automation/versions.yml`.
The backend version is read from `backend/version.py`.

### Running the tests
Install the pytest plugin `pytest-aiohttp`.

Execute the tests with:

```sh
python -m pytest
```

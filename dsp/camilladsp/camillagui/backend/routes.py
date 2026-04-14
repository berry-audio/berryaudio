from .settings import BASEPATH
from .statics import NoCacheStaticResource
from .views import (
    config_to_yml,
    delete_coeffs,
    delete_configs,
    download_coeffs_zip,
    download_configs_zip,
    eval_filter_values,
    eval_filterstep_values,
    get_config_at_gui_start,
    get_active_config_name,
    get_backends,
    get_capture_devices,
    get_config,
    get_config_file,
    get_default_config_file,
    get_defaults_for_coeffs,
    get_gui_config,
    get_gui_index,
    get_list_param,
    get_log_file,
    get_param,
    get_param_json,
    get_playback_devices,
    get_status,
    get_stored_coeffs,
    get_stored_configs,
    get_wav_info,
    parse_and_validate_yml_config_to_json,
    rename_coeff_file,
    rename_config_file,
    save_config_file,
    set_active_config_name,
    set_config,
    set_param,
    set_param_index,
    stop_processing,
    store_coeffs,
    store_configs,
    translate_convolver_to_json,
    translate_eqapo_to_json,
    validate_config,
    yaml_to_json,
)


def setup_routes(app):
    app.router.add_get("/api/status", get_status)
    app.router.add_get("/api/getparam/{name}", get_param)
    app.router.add_get("/api/getparamjson/{name}", get_param_json)
    app.router.add_get("/api/getlistparam/{name}", get_list_param)
    app.router.add_post("/api/setparam/{name}", set_param)
    app.router.add_post("/api/setparamindex/{name}/{index}", set_param_index)
    app.router.add_post("/api/evalfilter", eval_filter_values)
    app.router.add_post("/api/evalfilterstep", eval_filterstep_values)
    app.router.add_get("/api/getconfig", get_config)
    app.router.add_post("/api/setconfig", set_config)
    app.router.add_post("/api/stop", stop_processing)
    app.router.add_get("/api/getstartconfig", get_config_at_gui_start)
    app.router.add_get("/api/getactiveconfigfilename", get_active_config_name)
    app.router.add_get("/api/getdefaultconfigfile", get_default_config_file)
    app.router.add_post("/api/setactiveconfigfile", set_active_config_name)
    app.router.add_post("/api/configtoyml", config_to_yml)
    app.router.add_post(
        "/api/ymlconfigtojsonconfig", parse_and_validate_yml_config_to_json
    )
    app.router.add_post("/api/ymltojson", yaml_to_json)
    app.router.add_post("/api/convolvertojson", translate_convolver_to_json)
    app.router.add_post("/api/eqapotojson", translate_eqapo_to_json)
    app.router.add_post("/api/validateconfig", validate_config)
    app.router.add_get("/api/wavinfo", get_wav_info)
    app.router.add_get("/api/storedconfigs", get_stored_configs)
    app.router.add_get("/api/storedcoeffs", get_stored_coeffs)
    app.router.add_get("/api/defaultsforcoeffs", get_defaults_for_coeffs)
    app.router.add_post("/api/uploadconfigs", store_configs)
    app.router.add_post("/api/uploadcoeffs", store_coeffs)
    app.router.add_post("/api/deleteconfigs", delete_configs)
    app.router.add_post("/api/deletecoeffs", delete_coeffs)
    app.router.add_post("/api/renameconfig", rename_config_file)
    app.router.add_post("/api/renamecoeff", rename_coeff_file)
    app.router.add_post("/api/downloadconfigszip", download_configs_zip)
    app.router.add_post("/api/downloadcoeffszip", download_coeffs_zip)
    app.router.add_get("/api/guiconfig", get_gui_config)
    app.router.add_get("/api/getconfigfile", get_config_file)
    app.router.add_post("/api/saveconfigfile", save_config_file)
    app.router.add_get("/api/logfile", get_log_file)
    app.router.add_get("/api/capturedevices/{backend}", get_capture_devices)
    app.router.add_get("/api/playbackdevices/{backend}", get_playback_devices)
    app.router.add_get("/api/backends", get_backends)

    app.router.add_get("/", get_gui_index)


def setup_static_routes(app):
    # Set no-cache for html and css to make sure they get updated.
    # Without this browsers may continue running the old front end
    # from cache after the gui was upgraded to a new version.
    app.router.register_resource(
        NoCacheStaticResource(
            "/gui", BASEPATH / "build", file_endings=(".html", ".css")
        )
    )
    app.router.add_static("/config/", path=app["config_dir"])
    app.router.add_static("/coeff/", path=app["coeff_dir"])

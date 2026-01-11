import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { Form, Input, InputNumber } from "antd";
import { useConfigService } from "@/services/config";
import { DIALOG_EVENTS } from "@/store/constants";

import Page from "@/components/Page";
import SelectPcmDevices from "@/components/Form/SelectPcmDevices";
import SelectTimezone from "@/components/Form/SelectTimezone";
import ButtonSave from "@/components/Button/ButtonSave";

const SettingsGeneral = () => {
  const dispatch = useDispatch();
  const { getConfig, setConfig } = useConfigService();

  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      const config = await getConfig();

      form.setFieldsValue(config);
    })();
  }, []);

  const onFinish = async (data: any) => {
    setLoading(true);
    await setConfig(data);
    dispatch({ type: DIALOG_EVENTS.DIALOG_REBOOT });
    setLoading(false);
  };

  return (
    <Page
      backButton
      title="General"
      rightComponent={
        <div className="flex">
          <div className="mr-4">
            <ButtonSave onClick={() => form.submit()} isLoading={loading} />
          </div>
        </div>
      }
    >
      <div className="lg:px-0 px-6 py-3 lg:w-90">


         <SelectPcmDevices />
        {/* <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          className="w-full"
        >
          <Form.Item
            label={
              <div>
                <div className="font-bold">Hostname</div>
                <div className="text-secondary">
                 Name shown to others on the network.
                </div>
              </div>
            }
            name={["system", "hostname"]}
            rules={[{ required: true, message: "Hostname is required" }]}
          >
            <Input size="large" />
          </Form.Item>

          <Form.Item label={
              <div>
                <div className="font-bold">Output device</div>
                <div className=" text-secondary">
                  Your audio output device (DAC or loopback).
                </div>
              </div>
            } name={["playback", "output_device"]}>
            <SelectPcmDevices />
          </Form.Item>

           <SelectPcmDevices />

          <Form.Item
            label={
              <div>
                <div className="font-bold">Mixer Device</div>
                <div className=" text-secondary">
                  Volume control device. If no hardware volume is available, software control should be used.
                </div>
              </div>
            }
            name={["mixer", "mixer_device"]}
          >
            <SelectPcmDevices />
          </Form.Item>

          <Form.Item label={
              <div>
                <div className="font-bold">Initial Volume</div>
                <div className=" text-secondary">
                  The initial volume when the device starts
                </div>
              </div>
            } name={["mixer", "initial_volume"]}>
            <InputNumber min={0} max={100} size="large" />
          </Form.Item>

          <Form.Item label={
              <div>
                <div className="font-bold">Timezone</div>
                <div className=" text-secondary">
                  Select the Timezone to  display the current date & time on the player
                </div>
              </div>
            } name={["system", "timezone"]}>
            <SelectTimezone />
          </Form.Item>
        </Form> */}
      </div>
    </Page>
  );
};

export default SettingsGeneral;

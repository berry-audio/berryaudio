import { useEffect, useState } from "react";
import { useConfigService } from "@/services/config";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { useDispatch } from "react-redux";
import { DIALOG_EVENTS } from "@/store/constants";
import { z } from "zod";

import Page from "@/components/Page";
import SelectPcmDevices from "@/components/Form/SelectPcmDevices";
import SelectTimezone from "@/components/Form/SelectTimezone";
import ButtonSave from "@/components/Button/ButtonSave";

export const formSchema = z.object({
  system: z.object({
    hostname: z.string().min(1, "Hostname is required"),
    timezone: z.string().min(6, "Timezone is required"),
  }),
  mixer: z.object({
    output_device: z
      .string()
      .nullable()
      .refine((val) => val !== null && val.length > 0, {
        message: "Audio output device is required",
      }),
    output_audio: z
      .string()
      .nullable()
      .refine((val) => val !== null && val.length > 0, {
        message: "Audio output internal device is required",
      }),
    volume_device: z
      .string()
      .nullable()
      .refine((val) => val !== null && val.length > 0, {
        message: "Volume device is required",
      }),
  }),
});

const SettingsGeneral = () => {
  const dispatch = useDispatch();
  const { getConfig, setConfig } = useConfigService();

  const [loading, setLoading] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {},
  });

  useEffect(() => {
    (async () => {
      const _config = await getConfig();
      form.reset({ ..._config });
    })();
  }, []);

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    setLoading(true);
    await setConfig(values);
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
            <ButtonSave onClick={form.handleSubmit(onSubmit)} isLoading={loading} />
          </div>
        </div>
      }
    >
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 max-w-md">
          <div className="lg:px-0 px-6 py-3 lg:w-90">
            <div>
              <h2 className="mt-3 mb-3 text-xl">Device</h2>
            </div>

            <div className="mb-6">
              <FormField
                control={form.control}
                name="system.hostname"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-md block font-medium text-muted">Hostname</FormLabel>
                    <FormControl>
                      <Input placeholder="Device Name" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="mb-6">
              <FormField
                control={form.control}
                name="mixer.output_device"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-md block font-medium text-muted">Audio device</FormLabel>
                    <FormControl>
                      <SelectPcmDevices placeholder="Select Device" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="mb-6">
              <FormField
                control={form.control}
                name="mixer.volume_device"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-md block font-medium text-muted">Volume device</FormLabel>
                    <FormControl>
                      <SelectPcmDevices placeholder="Select Device" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div>
              <h2 className="mt-10  mb-3 text-xl">Date & Time</h2>
            </div>

            <div className="mb-6">
              <FormField
                control={form.control}
                name="system.timezone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-md block font-medium text-muted">Timezone</FormLabel>
                    <FormControl>
                      <SelectTimezone placeholder="Select Timezone" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </div>
        </form>
      </Form>
    </Page>
  );
};

export default SettingsGeneral;

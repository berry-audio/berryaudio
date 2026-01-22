import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { useConfigService } from "@/services/config";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Switch } from "@/components/ui/switch";
import { InputNumber } from "@/components/Form/InputNumber";
import { DIALOG_EVENTS } from "@/store/constants";
import { z } from "zod";

import Page from "@/components/Page";
import ButtonSave from "@/components/Button/ButtonSave";
import SelectCodec from "@/components/Form/SelectCodec";

export const formSchema = z.object({
  snapcast: z.object({
    server: z.boolean(),
    codec: z.string().min(1),
    chunk: z.number(),
    buffer: z.number(),
  }),
});

const SettingsSnapcast = () => {
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
      console.log(_config);
    })();
  }, []);

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    console.log(values);
    setLoading(true);
    await setConfig(values);
    dispatch({ type: DIALOG_EVENTS.DIALOG_REBOOT });
    setLoading(false);
  };

  return (
    <Page
      backButton
      title="Multiroom"
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
              <h2 className="mt-3 mb-3 text-xl">Server</h2>
            </div>

            <div className="mb-6">
              <FormField
                control={form.control}
                name="snapcast.server"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-md block font-medium text-muted">Enable Server</FormLabel>
                    <FormControl>
                      <Switch {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="mb-6">
              <FormField
                control={form.control}
                name="snapcast.codec"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-md block font-medium text-muted">Codec</FormLabel>
                    <FormControl>
                      <SelectCodec placeholder="Select Codec" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="mb-6">
              <FormField
                control={form.control}
                name="snapcast.chunk"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-md block font-medium text-muted">Chunk (ms)</FormLabel>
                    <FormControl>
                      <InputNumber {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="mb-6">
              <FormField
                control={form.control}
                name="snapcast.buffer"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-md block font-medium text-muted">Buffer</FormLabel>
                    <FormControl>
                      <InputNumber {...field} />
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

export default SettingsSnapcast;

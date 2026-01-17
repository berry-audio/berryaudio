import { useEffect, useState } from "react";
import { useConfigService } from "@/services/config";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { z } from "zod";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";

import Page from "@/components/Page";
import SelectPcmDevices from "@/components/Form/SelectPcmDevices";
import SelectTimezone from "@/components/Form/SelectTimezone";
import ButtonSave from "@/components/Button/ButtonSave";


export const formSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

const SettingsGeneral = () => {
  const { getConfig } = useConfigService();

  const [loading] = useState(false);

  useEffect(() => {
    (async () => {
      const config = await getConfig();
      console.log(config);
    })();
  }, []);

  // const onFinish = async (data: any) => {
  //   setLoading(true);
  //   await setConfig(data);
  //   dispatch({ type: DIALOG_EVENTS.DIALOG_REBOOT });
  //   setLoading(false);
  // };

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    console.log(values);
  }

  return (
    <Page
      backButton
      title="General"
      rightComponent={
        <div className="flex">
          <div className="mr-4">
            <ButtonSave onClick={() => undefined} isLoading={loading} />
          </div>
        </div>
      }
    >
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 max-w-md">
          {/* Email */}
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input placeholder="you@example.com" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="lg:px-0 px-6 py-3 lg:w-90">
            <div>
              <h2 className="mt-3 mb-3 text-xl">Device</h2>
            </div>

            <div className="mb-6">
              <label className="mb-2 block font-medium text-muted">Hostname</label>
              <Input name="hostname" value={''} />
            </div>

            <div className="mb-6">
              <label className="mb-2 block font-medium text-muted">Output audio device</label>
              <SelectPcmDevices />
            </div>
            <div className="mb-6">
              <label className="mb-2 block font-medium text-muted">Mixer Volume Device</label>
              <SelectPcmDevices />
            </div>

            <div>
              <h2 className="mt-10  mb-3 text-xl">Date & Time</h2>
            </div>
            <div className="mb-6">
              <label className="mb-2 block font-medium text-muted">Timezone</label>
              <SelectTimezone />
            </div>
          </div>
           {/* <Button type="submit">Submit</Button> */}
        </form>
      </Form>
    </Page>
  );
};

export default SettingsGeneral;

import {
  BrowserRouter as Router,
  Routes,
  Route,
} from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeProvider";
import { Provider } from "react-redux";
import { store } from "./store";

import Local from "./views/Local";
import Storage from "./views/Storage";
import Start from "./views/Start";
import Layout from "./layout";
import Queue from "./views/Queue";
import Settings from "./views/Settings";
import SettingsAbout from "./views/Settings/SettingsAbout";
import Radio from "./views/Radio";
import Playlists from "./views/Playlist";
import SettingsGeneral from "./views/Settings/SettingsGeneral";
import SettingsLibrary from "./views/Settings/SettingsLibrary";
import SettingsBluetooth from "./views/Settings/SettingsBluetooth";
import SettingsNetwork from "./views/Settings/SettingsNetwork";
import SettingsSnapcast from "./views/Settings/SettingsSnapcast";

const App = () => {
  return (
    <ThemeProvider>
      <Provider store={store}>
          <Router>
              <Layout>
                <Routes key={location.pathname}>
                  <Route path="/" element={<Start />} />
                  <Route path="/bluetooth" element={<SettingsBluetooth />} />
                  <Route path="/spotify" element={<Start />} />
                  <Route path="/shairportsync" element={<Start />} />
                  <Route path="/snapcast" element={<SettingsSnapcast />} />
                  <Route path="/queue" element={<Queue />} />
                  <Route path="/playlist/:id?" element={<Playlists />} />
                  <Route path="/library/:view?/:id?" element={<Local />} />
                  <Route path="/radio" element={<Radio />} />
                  <Route path="/storage/*" element={<Storage />} />
                  <Route path="/settings/" element={<Settings />} />
                  <Route path="/settings/about/" element={<SettingsAbout />} />
                  <Route path="/settings/general/" element={<SettingsGeneral />} />
                  <Route path="/settings/library/" element={<SettingsLibrary />} />
                  <Route path="/settings/bluetooth/" element={<SettingsBluetooth />} />
                  <Route path="/settings/network/" element={<SettingsNetwork />} />
                </Routes>
              </Layout>
          </Router>
      </Provider>
    </ThemeProvider>
  );
};

export default App;

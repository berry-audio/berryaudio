const { app, BrowserWindow } = require('electron');

function createWindow() {
  const win = new BrowserWindow({
    width: 640,
    height: 480,
    fullscreen: true, 
    kiosk: true,  
    webPreferences: {
      zoomFactor: 1.4,
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  
  win.loadURL('http://192.168.1.105:5173'); // replace with your app URL
  //win.loadURL('http://localhost:8080'); // replace with your app URL
  //win.loadFile('index.html'); // if you have a local HTML file
  win.webContents.setZoomFactor(1.4)
  win.webContents.insertCSS('* { cursor: none !important; }');
  win.webContents.on('dom-ready', () => {
  win.webContents.insertCSS('* { cursor: none !important; }');
});

}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

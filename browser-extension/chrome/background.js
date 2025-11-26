chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === 'upload_attempt') {
    console.log('Upload attempt', msg);
    // For production, use chrome.runtime.connectNative to send to native host:
    // const port = chrome.runtime.connectNative('com.company.upload_detector');
    // port.postMessage(msg);
  }
});

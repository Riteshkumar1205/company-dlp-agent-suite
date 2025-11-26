function handleFileInput(el) {
  el.addEventListener('change', (e) => {
    const files = e.target.files;
    if (files && files.length) {
      const entries = Array.from(files).map(f => ({name: f.name, size: f.size, type: f.type}));
      chrome.runtime.sendMessage({type: 'upload_attempt', files: entries, url: location.href});
    }
  });
}
document.querySelectorAll('input[type=file]').forEach(handleFileInput);
const obs = new MutationObserver(muts => {
  muts.forEach(m => {
    m.addedNodes.forEach(n => {
      if (n.querySelectorAll) {
        n.querySelectorAll('input[type=file]').forEach(handleFileInput);
      }
    });
  });
});
obs.observe(document, {childList: true, subtree: true});
window.addEventListener('drop', (e) => {
  const dt = e.dataTransfer;
  if (dt && dt.files && dt.files.length) {
    const entries = Array.from(dt.files).map(f => ({name: f.name, size: f.size, type: f.type}));
    chrome.runtime.sendMessage({type: 'upload_attempt', files: entries, url: location.href});
  }
});

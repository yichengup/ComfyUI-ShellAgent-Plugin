import { app } from "../../scripts/app.js";
app.registerExtension({
  name: "Shellagent.extension",
  async setup() {
    window.parent.postMessage({
      type: 'loaded'
    }, '*');
    window.addEventListener('message', (event) => {
      if (event.data.type === 'save') {
        app.graphToPrompt().then(data => {
          window.parent.postMessage({
            prompt: data?.output || {},
            workflow: data?.workflow || {},
            type: 'save'
          }, "*");
        });
      }
      if (event.data.type === 'load') {
        app.loadGraphData(event.data.data, true, false);
      }
    });
  },
});
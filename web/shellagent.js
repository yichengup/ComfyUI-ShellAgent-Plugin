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
			if (event.data.type === 'load_default') {
				// 使用FileReader读取JSON文件
				fetch('extensions/ComfyUI-ShellAgent-Plugin/shellagent_default.json')
					.then(response => response.blob())
					.then(blob => {
						const reader = new FileReader();
						reader.onload = function(e) {
							const json = JSON.parse(e.target.result);
							app.loadGraphData(json, true, false);
						};
						reader.readAsText(blob);
					})
					.catch(error => console.error('加载默认JSON文件时出错:', error));
			}
    });
  },
});
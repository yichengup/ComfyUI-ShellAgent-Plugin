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
});app.registerExtension({
  name: "Comfy.ShellAgent.UploadImage",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name === "ShellAgentPluginInputImage") {
      if (
        nodeData?.input?.required?.default_value?.[1]?.image_upload === true
      ) {
        nodeData.input.required.upload = [
          "IMAGEUPLOAD",
          { widget: "default_value" },
        ];
      }
    }

    if (nodeData.name.indexOf('ShellAgentPlugin') === -1) {
      addMenuHandler(nodeType, function (_, options) {
        if (this.widgets) {
          let toInput = [];

          for (const w of this.widgets) {
            if (["customtext"].indexOf(w.type) > -1) {
              toInput.push({
                content: `Input Text -> ${w.name}`,
                callback: () => {
                  alert('Not implemented')
                }
              })
            }
          }

          if (toInput.length) {
            options.unshift({
              content: "Convert to ShellAgent",
              submenu: {
                options: toInput
              }
            })
          }
        }
      })
    }
  },
});

function addMenuHandler(nodeType, cb) {
  const getOpts = nodeType.prototype.getExtraMenuOptions;
  nodeType.prototype.getExtraMenuOptions = function () {
    const r = getOpts.apply(this, arguments);
    cb.apply(this, arguments);
    return r;
  };
}
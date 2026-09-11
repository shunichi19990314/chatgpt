const urlInput = document.querySelector("#url");
const inspectButton = document.querySelector("#inspect");
const downloadButton = document.querySelector("#download");
const error = document.querySelector("#error");
const preview = document.querySelector("#preview");
const format = document.querySelector("#format");

function showError(message = "") { error.textContent = message; }
function setLoading(button, loading, label) { button.disabled = loading; button.textContent = loading ? "確認中…" : label; }

inspectButton.addEventListener("click", async () => {
  const url = urlInput.value.trim();
  showError(); preview.hidden = true; format.disabled = true; downloadButton.disabled = true;
  setLoading(inspectButton, true, "確認する");
  try {
    const response = await fetch("/api/info", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    document.querySelector("#thumbnail").src = data.thumbnail || "";
    document.querySelector("#thumbnail").alt = `${data.title} のサムネイル`;
    document.querySelector("#title").textContent = data.title;
    document.querySelector("#channel").textContent = data.channel;
    preview.hidden = false; format.disabled = false; downloadButton.disabled = false;
  } catch (err) { showError(err.message || "情報を取得できませんでした。"); }
  finally { setLoading(inspectButton, false, "確認する"); }
});

downloadButton.addEventListener("click", () => {
  const mode = document.querySelector('input[name="mode"]:checked').value;
  const form = document.createElement("form");
  form.method = "POST"; form.action = "/api/download"; form.hidden = true;
  [["url", urlInput.value.trim()], ["mode", mode]].forEach(([name, value]) => {
    const field = document.createElement("input"); field.name = name; field.value = value; form.append(field);
  });
  document.body.append(form); form.submit(); form.remove();
});

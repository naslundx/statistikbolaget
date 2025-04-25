const form = document.getElementById("queryForm");
const submitBtn = document.getElementById("submitButton");
const input = document.getElementById("questionInput");
const historyDiv = document.getElementById("history");
const clearAllButtonContainer = document.getElementById(
  "clearAllButtonContainer",
);

var idCounter = 0;
let history = JSON.parse(localStorage.getItem("chatHistory") || "[]");
renderExistingHistory();

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) {
    return;
  }

  submitBtn.classList.add("opacity-50", "cursor-not-allowed");
  addHistoryLoader();

  const raw_result = await fetch("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  const result = await raw_result.json();
  result.id = idCounter++;
  console.log(result);
  history.push(result);
  saveHistoryToLocalStorage();
  input.value = "";

  removeHistoryLoader();
  renderHistoryItem(result);

  submitBtn.classList.remove("opacity-50", "cursor-not-allowed");
});

function removeHistoryLoader() {
  document.querySelectorAll(".history-temp").forEach((e) => e.remove());
}

function saveHistoryToLocalStorage() {
  localStorage.setItem("chatHistory", JSON.stringify(history));
}

function addHistoryLoader() {
  let container = document.createElement("div");
  container.className = "history-temp bg-white shadow p-4 m-4 rounded-lg";

  const div = document.createElement("div");
  div.className = "loader m-auto";

  container.appendChild(div);
  historyDiv.insertBefore(container, historyDiv.firstChild);
}

function renderHistoryItem(entry) {
  const container = document.createElement("div");
  container.className = "bg-white shadow p-4 m-4 rounded-lg";

  const question = document.createElement("a");
  question.className = "font-semibold mb-2";
  question.textContent = `${entry.question}`;
  question.onclick = () => populateEntry(entry.id);
  container.appendChild(question);

  const removeBtn = document.createElement("button");
  removeBtn.textContent = "✖";
  removeBtn.className = "ml-2 text-red-500 hover:text-red-700 text-sm";
  removeBtn.onclick = () => removeEntry(entry.id);
  container.appendChild(removeBtn);

  const sqlButton = document.createElement("button");
  sqlButton.className = "collapsible bg-gray-200 hover:bg-gray-300";
  sqlButton.textContent = "SQL";
  const sql = document.createElement("pre");
  sql.className = "content bg-gray-100 p-2 rounded text-sm overflow-wrap";
  sql.textContent = entry.sql.trim();

  if (entry.success) {
    const result = document.createElement("div");
    result.className = "wrap-break-word mb-10";
    result.innerHTML = entry.result;
    container.appendChild(result);
  }

  const rawResultButton = document.createElement("button");
  rawResultButton.className = "collapsible bg-gray-200 hover:bg-gray-300";
  rawResultButton.textContent = "Raw result";
  const rawResult = document.createElement("div");
  rawResult.className = "content wrap-break-word";
  rawResult.innerHTML = entry.raw_result;
  container.appendChild(rawResultButton);
  container.appendChild(rawResult);

  if (!entry.success) {
    rawResultButton.className = "collapsible bg-red-200 hover:bg-red-300";
    rawResult.className =
      "content bg-red-100 p-2 rounded text-sm overflow-wrap";
  }

  historyDiv.insertBefore(container, historyDiv.firstChild);

  clearAllButtonContainer.classList.remove("hidden");
  setCollapsibleCallbacks();
}

function renderExistingHistory() {
  historyDiv.innerHTML = "";
  let largestId = 0;
  history.forEach((e) => {
    renderHistoryItem(e);
    largestId = Math.max(largestId, e.id);
  });
  idCounter = largestId + 1;
  setCollapsibleCallbacks();
}

function removeEntry(id) {
  const index = history.findIndex((e) => e.id == id);
  if (index < 0) {
    return;
  }

  history.splice(index, 1);
  historyDiv.children[historyDiv.children.length - index - 1].remove();

  if (history.length === 0) {
    clearAllButtonContainer.classList.add("hidden");
  }
  saveHistoryToLocalStorage();
}

function populateEntry(id) {
  const index = history.findIndex((e) => e.id == id);
  input.value = history[index].question;
}

function setCollapsibleCallbacks() {
  Array.from(document.getElementsByClassName("collapsible"))
    .filter((e) => !e.classList.contains("has-event-listener"))
    .forEach((e) => {
      e.classList.add("has-event-listener");

      e.addEventListener("click", function () {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.display === "block") {
          content.style.display = "none";
        } else {
          content.style.display = "block";
        }
      });
    });
}

function clearAllHistory() {
  localStorage.setItem("chatHistory", []);
  history = [];
  renderExistingHistory();
  clearAllButtonContainer.classList.add("hidden");
}

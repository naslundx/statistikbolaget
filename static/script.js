const form = document.getElementById("queryForm");
const submitBtn = document.getElementById("submitButton");
const input = document.getElementById("questionInput");
const historyDiv = document.getElementById("history");

let history = JSON.parse(localStorage.getItem("chatHistory") || "[]");
renderHistory();

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) return;

  submitBtn.classList.add("opacity-50", "cursor-not-allowed");

  const raw_result = await fetch("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  const result = await raw_result.json();
  console.log(result);
  history.push(result);
  localStorage.setItem("chatHistory", JSON.stringify(history));
  input.value = "";
  renderHistory();

  submitBtn.classList.remove("opacity-50", "cursor-not-allowed");
});

function renderHistory() {
  historyDiv.innerHTML = "";
  history
    .slice()
    .reverse()
    .forEach((entry, i) => {
      const originalIndex = history.length - 1 - i;
      const container = document.createElement("div");
      container.className = "bg-white shadow p-4 m-4 rounded-lg";

      const removeBtn = document.createElement("button");
      removeBtn.textContent = "✖";
      removeBtn.className =
        "top-2 right-2 text-red-500 hover:text-red-700 text-sm";
      removeBtn.onclick = () => removeEntry(originalIndex);

      const question = document.createElement("a");
      question.className = "font-semibold text-blue-700 mb-2";
      question.textContent = `${entry.question}`;
      question.onclick = () => populateEntry(originalIndex);

      const sqlButton = document.createElement("button");
      sqlButton.className = "collapsible bg-gray-200 hover:bg-gray-300";
      sqlButton.textContent = "SQL";
      const sql = document.createElement("pre");
      sql.className = "content bg-gray-100 p-2 rounded text-sm overflow-wrap";
      sql.textContent = entry.sql.trim();

      let errorButton = null;
      let error = null;
      if (entry.error_msg) {
        errorButton = document.createElement("button");
        errorButton.className = "collapsible bg-red-200 hover:bg-red-300";
        errorButton.textContent = "Error";
        error = document.createElement("div");
        error.className =
          "content bg-red-100 p-2 rounded text-sm overflow-wrap";
        error.textContent = entry.error_msg;
      }

      const result = document.createElement("div");
      result.className = "wrap-break-word mb-10";
      result.innerHTML = entry.result;

      const rawResultButton = document.createElement("button");
      rawResultButton.className = "collapsible bg-gray-200 hover:bg-gray-300";
      rawResultButton.textContent = "Raw result";
      const rawResult = document.createElement("div");
      rawResult.className = "content wrap-break-word";
      rawResult.innerHTML = entry.raw_result;

      container.appendChild(question);
      container.appendChild(removeBtn);

      if (errorButton) {
        container.appendChild(errorButton);
        container.appendChild(error);
      } else {
        container.appendChild(result);
        container.appendChild(rawResultButton);
        container.appendChild(rawResult);
        container.appendChild(sqlButton);
        container.appendChild(sql);
      }

      historyDiv.appendChild(container);
    });
  setCollapsibleCallbacks();
}

function removeEntry(index) {
  history.splice(index, 1);
  renderHistory();
}

function populateEntry(index) {
  input.value = history[index].question;
}

function setCollapsibleCallbacks() {
  var coll = document.getElementsByClassName("collapsible");
  for (let i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function () {
      this.classList.toggle("active");
      var content = this.nextElementSibling;
      if (content.style.display === "block") {
        content.style.display = "none";
      } else {
        content.style.display = "block";
      }
    });
  }
}

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

async function postVote(uuid, upvote) {
  const raw_result = await fetch("/vote", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ uuid, upvote }),
  });
  const result = await raw_result.json();
  console.log(result);
}

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

function createCheckboxWithLabel(
  labelText,
  checkboxClasses = [],
  labelClasses = [],
) {
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.classList.add(...checkboxClasses);

  const label = document.createElement("label");
  label.textContent = labelText;
  label.classList.add(...labelClasses);

  const id = `checkbox-${Math.random().toString(36).substr(2, 9)}`;
  checkbox.id = id;
  label.setAttribute("for", id);

  return { checkbox, label };
}

function renderHistoryItem(entry) {
  const container = document.createElement("div");
  container.dataset.id = entry.id;
  container.className = "bg-white shadow p-4 m-4 rounded-lg";

  const question = document.createElement("a");
  question.className = "font-semibold mb-2 hover:text-blue-700";
  question.textContent = `${entry.question}`;
  question.onclick = () => populateEntry(entry.id);
  container.appendChild(question);

  const removeBtn = document.createElement("a");
  removeBtn.textContent = "[x]";
  removeBtn.className = "ml-2 text-red-400 hover:text-red-700 text-sm";
  removeBtn.onclick = () => removeEntry(entry.id);
  container.appendChild(removeBtn);

  if (entry.success) {
    const result = document.createElement("div");
    result.className = "wrap-break-word mb-6";
    result.innerHTML = entry.result;
    container.appendChild(result);

    const votes = document.createElement("div");
    votes.className = "votes";
    const upvote = document.createElement("i");
    upvote.className =
      entry.vote === "up" ? "fa fa-thumbs-up" : "fa fa-thumbs-o-up";
    upvote.onclick = () => vote(entry.id, "up");
    votes.appendChild(upvote);
    const downvote = document.createElement("i");
    downvote.className =
      entry.vote === "down" ? "fa fa-thumbs-down" : "fa fa-thumbs-o-down";
    downvote.onclick = () => vote(entry.id, "down");
    votes.appendChild(downvote);
    container.appendChild(votes);
  } else {
    container.classList.remove("bg-white");
    container.classList.add("bg-red-100");

    const result = document.createElement("div");
    result.className = "";
    result.innerHTML = "Något blev fel, försök igen.";
    container.appendChild(result);
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

function findEntryIndex(id) {
  return history.findIndex((e) => e.id == id);
}

function removeEntry(id) {
  const index = findEntryIndex(id);
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

function vote(id, what) {
  let historyElement = history[findEntryIndex(id)];

  const upvote = document.querySelector(`[data-id="${id}"] i:first-child`);
  const downvote = document.querySelector(`[data-id="${id}"] i:last-child`);

  if (what === historyElement.vote) {
    return;
  }

  upvote.className = "fa fa-thumbs-o-up";
  downvote.className = "fa fa-thumbs-o-down";

  if (what === "up") {
    upvote.className = "fa fa-thumbs-up";
    historyElement.vote = "up";
    postVote(historyElement.uuid, true);
  } else if (what === "down") {
    downvote.className = "fa fa-thumbs-down";
    historyElement.vote = "down";
    postVote(historyElement.uuid, false);
  }

  saveHistoryToLocalStorage();
}

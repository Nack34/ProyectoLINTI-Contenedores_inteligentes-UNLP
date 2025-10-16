const btn = document.getElementById("btn");
const result = document.getElementById("result");
const loading = document.getElementById("loading");

function predecir() {
  fetch(`/start_analyzing`);
  btn.disabled = true;
  result.style.display = "none";
  loading.style.display = "block";
}

const eventSource = new EventSource("/stream/result/");
eventSource.onmessage = function (event) {
  result.innerText = event.data;
};

const eventQR = new EventSource("/stream/qr/");
eventQR.onmessage = function (event) {
  if (event.data === "True") {
    loadQr();
    loading.style.display = "none";
    result.style.display = "block";
    // The button is re-enabled after the QR code disappears
  }
};

const initialPredictionEvents = new EventSource("/stream/initial_prediction_status/");
initialPredictionEvents.onmessage = function (event) {
  if (event.data === "true") {
    btn.disabled = false;
    initialPredictionEvents.close();
  }
};

async function loadQr() {
  try {
    const response = await fetch("/qr/");
    if (!response.ok) return;

    const blob = await response.blob();
    const imgUrl = URL.createObjectURL(blob);

    const qrContainer = document.querySelector(".qr");
    qrContainer.querySelector("#qr").src = imgUrl;
    qrContainer.style.display = "block";

    setTimeout(() => {
      qrContainer.style.display = "none";
      URL.revokeObjectURL(imgUrl);
      btn.disabled = false; // Re-enable button
    }, 5000); // 5 seconds
  } catch (e) {
    console.error("Could not load QR", e);
  }
}

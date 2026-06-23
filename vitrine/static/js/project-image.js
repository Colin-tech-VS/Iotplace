// Project image drag & drop — client-side preview only.
// The file is uploaded with the multipart form on submit (name="image").
(function () {
  "use strict";

  var root = document.getElementById("projectImageUpload");
  if (!root) return;

  var input = document.getElementById("projectImageInput");
  var drop = document.getElementById("projectImageDrop");
  var browse = document.getElementById("projectImageBrowse");
  var preview = document.getElementById("projectImagePreview");
  var img = document.getElementById("projectImageImg");
  var removeBtn = document.getElementById("projectImageRemove");
  var removeFlag = document.getElementById("projectImageRemoveFlag");

  var MAX_BYTES = 2 * 1024 * 1024;
  var ALLOWED = ["image/png", "image/jpeg", "image/webp"];

  function showPreview(src) {
    if (img) {
      img.src = src;
      img.hidden = false;
    }
    if (preview) preview.classList.remove("is-empty");
    if (removeBtn) removeBtn.hidden = false;
  }

  function applyFile(file) {
    if (!file) return;
    if (ALLOWED.indexOf(file.type) === -1) {
      alert("Format non supporté (PNG, JPEG ou WebP).");
      return;
    }
    if (file.size > MAX_BYTES) {
      alert("Image trop volumineuse (max 2 Mo).");
      return;
    }
    // Put the dropped file into the form input so it is submitted.
    if (input && window.DataTransfer) {
      var dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
    }
    if (removeFlag) removeFlag.value = "";
    var reader = new FileReader();
    reader.onload = function (e) {
      showPreview(e.target.result);
    };
    reader.readAsDataURL(file);
  }

  if (browse && input) {
    browse.addEventListener("click", function () {
      input.click();
    });
  }

  if (input) {
    input.addEventListener("change", function () {
      if (input.files && input.files[0]) applyFile(input.files[0]);
    });
  }

  if (drop) {
    drop.addEventListener("click", function (e) {
      if (e.target === browse || e.target === removeBtn) return;
      if (input) input.click();
    });
    drop.addEventListener("keydown", function (e) {
      if ((e.key === "Enter" || e.key === " ") && input) {
        e.preventDefault();
        input.click();
      }
    });
    ["dragenter", "dragover"].forEach(function (evt) {
      drop.addEventListener(evt, function (e) {
        e.preventDefault();
        drop.classList.add("drag-over");
      });
    });
    ["dragleave", "drop"].forEach(function (evt) {
      drop.addEventListener(evt, function (e) {
        e.preventDefault();
        drop.classList.remove("drag-over");
      });
    });
    drop.addEventListener("drop", function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      if (files && files[0]) applyFile(files[0]);
    });
  }

  if (removeBtn) {
    removeBtn.addEventListener("click", function () {
      if (input) input.value = "";
      if (img) {
        img.src = "";
        img.hidden = true;
      }
      if (preview) preview.classList.add("is-empty");
      removeBtn.hidden = true;
      if (removeFlag) removeFlag.value = "1";
    });
  }
})();

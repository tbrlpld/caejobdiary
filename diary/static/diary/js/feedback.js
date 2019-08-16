/* global $ document */

function copyEmailAddress() {
  // See: https://www.w3schools.com/howto/howto_js_copy_clipboard.asp
  const copyText = $('.feedback-modal-email-display');
  console.log(`Copied email address: ${copyText}`);
  console.log(copyText);
  /* Select the text field */
  copyText.select();
  /* Copy the text inside the text field */
  document.execCommand('copy');
}


$('document').ready(() => {
  $('#feedback-email-link').tooltip(); // Enabling tooltips on the element
  $('#feedback-email-copy-button').tooltip(); // Enabling tooltips on the element
  $('#email-copy-button').click(copyEmailAddress);
});

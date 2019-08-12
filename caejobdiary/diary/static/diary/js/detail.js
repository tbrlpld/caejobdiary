/* global $ */

function changeSuccessMessageDisappearAfterTimeout() {
  const changeSuccessObj = $('#changes-success');
  console.log('Checking if messages exist');
  if (changeSuccessObj.length) {
    console.log('Messages exist');
    console.log('Starting timeout');
    setTimeout(() => {
      console.log('Timer up');
      changeSuccessObj.fadeOut();
      console.log('Messages hidden');
    }, 10000);
  } else {
    console.log('No messages');
  }
}

function showWarningIfAssessmentObsolete() {
  const assessment = $('#id_result_assessment');
  console.log(assessment.val());
  if (assessment.val() === 'obs') {
    $('#obsolete_warning').slideDown();
  } else {
    $('#obsolete_warning').slideUp();
  }
}

function showObsoleteWarningOnAssessmentChange() {
  $('#id_result_assessment').on('change', showWarningIfAssessmentObsolete);
}

function showUnsavedChangesInfoOnFormChange() {
  const detailForm = $('#detail-form');
  const unsavedChangesMsg = $('#unsaved-changes-msg');
  // get initial form string
  const initialFormString = detailForm.serialize();
  $('#detail-form').on('change', () => {
    console.log('Form change!');
    // get new form string
    const newFormString = detailForm.serialize();
    // get current message visibility
    const currentlyVisible = unsavedChangesMsg.is(':visible');
    console.log(`Visibility of unsaved changes message: ${currentlyVisible}`);
    // if form strings differ and message not visible
    if (initialFormString !== newFormString && !currentlyVisible) {
      // show unsave change info
      console.log('Form changed and message not shown');
      unsavedChangesMsg.slideDown();
    // else if strings the same but message visible
    } else if (initialFormString === newFormString && currentlyVisible) {
      // hide message
      console.log('Form unchanged, but message is shown');
      unsavedChangesMsg.slideUp();
    }
  });
}

function reloadPageOnFormReset() {
  // The reset function does not seem to trigger the typical change functions.
  // To get around this, you can just reload the page.
  $('#detail-form #reset-button').on('click', () => {
    console.log('Reset clicked');
    window.location.reload();
  });
}

$(document).ready(() => {
  // Resetting the form. Some browsers do no throw out the changes from a
  // previous load.
  $('#detail-form').trigger('reset');

  changeSuccessMessageDisappearAfterTimeout();
  showWarningIfAssessmentObsolete();
  // Event Listeners
  showObsoleteWarningOnAssessmentChange();
  showUnsavedChangesInfoOnFormChange();
  reloadPageOnFormReset();
});

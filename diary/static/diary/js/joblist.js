
function setPointerCursorForWrappedText(){
	var wrappableTexts = $(".text-wrappable")
	for (var i = wrappableTexts.length - 1; i >= 0; i--) {
		var wrappableText = wrappableTexts[i]
		console.log("Wrappable: ", wrappableText);
		var hasOverflow = Math.ceil($(wrappableText).innerWidth()) < Math.floor(wrappableText.scrollWidth);
		console.log("Has overflow: ", hasOverflow);
		var isWrapped = $(wrappableText).hasClass("text-wrap");
		var toggler = $(wrappableText).parents(".text-wrap-toggler");
		console.log("Toggler: ", toggler);
		if (hasOverflow | isWrapped) {
			$(toggler).css("cursor", "pointer");
			$(toggler).on("click", function(){
				console.log("Wrap toggler was clicked.", this)
				toggleTextWrap(this);
			});
		};
	};
};

function eventsForSetPointerCursorForWrapped(){
	setPointerCursorForWrappedText()
	$(window).resize(function(){
		$(".text-wrap-toggler").css("cursor", "initial");
		$(".text-wrap-toggler").off("click");
		setPointerCursorForWrappedText();
	});
};

function toggleTextWrap(toggler){
	console.log("Toggling wrapped text.");
	textWrapContainer = $(toggler).parents(".text-wrap-container");
	console.log("Container: ", textWrapContainer);
	wrappable = $(textWrapContainer).find(".text-wrappable");
	console.log("Wrappable: ", wrappable);
	$(wrappable).toggleClass("text-wrap")
};

$(eventsForSetPointerCursorForWrapped);
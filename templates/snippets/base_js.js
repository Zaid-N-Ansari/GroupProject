function preloadCallback(src, elmID) {
	const img = document.getElementById(elmID);
	img.src = src;
}

function preloadImg(imgSrc, elmID) {
	const ImagePreload = new Image();
	ImagePreload.src = imgSrc;

	if (ImagePreload.complete) {
		preloadCallback(ImagePreload.src, elmID);
		ImagePreload.onload = function () { }
	}
	else {
		ImagePreload.onload = function () {
			preloadCallback(ImagePreload.src, elmID);
			ImagePreload.onload = function () { }
		}
	}
}

function validateText(str) {
	const md = window.markdownit({
		highlight: function (str, lang) {
			if (lang && hljs.getLanguage(lang)) {
				try {
					return '<pre><code class="hljs">' +
						hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
						'</code></pre>';
				} catch (__) { }
			}
			return '<pre><code class="hljs">' + md.utils.escapeHtml(str) + '</code></pre>';
		},
		linkify: true,
	});
	const result = md.render(str);
	return result;
}
(function (global) {
    'use strict';

    var timestamp = parseInt(document.getElementById('mock-now').attributes['data-mockNow-timestamp'].value) * 1000;
    var url = document.getElementById('mock-now').attributes['data-mockNow-url'].value;
    document.addEventListener("DOMContentLoaded", function (event) {
        // create css style
        var createElement = function(tag) {
            return document.createElement(tag);
        }

        var style = createElement('style');
        style.innerText = '.mock-now-wrapper {position: fixed; height: 2em; padding: 5px; bottom: 10px; right: 10px; font-size: 12px; color: black}'
        document.head.appendChild(style);

        var wrapper = createElement('div');
        wrapper.classList.add('mock-now-wrapper');
        var setWrapperHtml = function(timestamp) {
            wrapper.innerHTML = 'Server time: ' + new Date(timestamp) + " <a href='" + url + "'>Change</a>";
        }
        document.body.appendChild(wrapper);
        setInterval(function() {
            timestamp += 1000;
            setWrapperHtml(timestamp);
        }, 1000)
        setWrapperHtml(timestamp);
    });
})(this);
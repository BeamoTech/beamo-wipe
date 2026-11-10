"""Keyboard method selection keeps focus on the rebuilt choice."""

import shutil
import subprocess

import pytest

from beamo_wipe.gallery import gallery_html
from preview_page import inline_script


def test_keyboard_method_selection_keeps_focus():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable")
    script = inline_script(gallery_html())
    method = script.index('} else if (screen === "method")')
    start = script.index('    main.querySelectorAll(".card.pickable").forEach(el => {', method)
    end = script.index('    main.querySelector("#limits")', start)
    handler = script[start:end]
    program = """
let method = 'everyday';
let active = {id: 'body'};
let redraws = 0;
const oldCard = {dataset: {id: 'extra'}, focus() { active = this; }};
const newCard = {dataset: {id: 'extra'}, focus() { active = this; }};
let cards = [oldCard];
const main = {
  querySelectorAll() { return cards; },
  querySelector(selector) {
    return selector === '[data-id="extra"]' ? cards[0] : null;
  },
};
function draw() { redraws += 1; cards = [newCard]; active = {id: 'body'}; }
""" + handler + """
oldCard.focus();
oldCard.onkeydown({key: ' ', repeat: false, preventDefault() {}});
if (method !== 'extra') throw Error('method did not change');
if (active !== newCard) throw Error('keyboard focus was lost after method selection');
oldCard.onkeydown({key: ' ', repeat: true, preventDefault() {}});
if (redraws !== 1) throw Error('held Space redrew the method choice');
"""
    result = subprocess.run([node, "-e", program], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def _function(script, name):
    start = script.index(f"function {name}(")
    depth, index = 0, script.index("{", start)
    while True:
        depth += {"{": 1, "}": -1}.get(script[index], 0)
        if depth == 0:
            return script[start:index + 1]
        index += 1


def test_keyboard_setup_choices_keep_focus():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable")
    script = inline_script(gallery_html())
    start = script.index('    main.querySelectorAll("[data-layout]").forEach(el => {')
    end = script.index('    const box = main.querySelector("#kbcheck")', start)
    handlers = script[start:end]
    # #155: a layout pick runs the production layoutChanged(); away from
    # Confirm it still starts over (owner tick, entry and disk cleared).
    # #179: the contrast choices are a third group that must keep focus too.
    program = """
let keyboardLayout = 'us', layoutChosen = false, owner = true, token = 'old', selected = {};
let keyboardFrom = null, confirmMismatch = false;
function tokenOk() { return false; }
let textSize = 'standard', highContrast = false, active = {id: 'body'};
const oldLayout = {dataset: {layout: 'fr'}, focus() { active = this; }};
const newLayout = {dataset: {layout: 'fr'}, focus() { active = this; }};
const oldSize = {dataset: {text: 'large'}, focus() { active = this; }};
const newSize = {dataset: {text: 'large'}, focus() { active = this; }};
const oldContrast = {dataset: {contrast: 'true'}, focus() { active = this; }};
const newContrast = {dataset: {contrast: 'true'}, focus() { active = this; }};
let layouts = [oldLayout], sizes = [oldSize], contrasts = [oldContrast];
const main = {
  querySelectorAll(selector) {
    if (selector === '[data-layout]') return layouts;
    if (selector === '[data-text]') return sizes;
    if (selector === '[data-contrast]') return contrasts;
    throw Error('unexpected selector ' + selector);
  },
  querySelector(selector) {
    if (selector === '[data-layout="fr"]') return layouts[0];
    if (selector === '[data-text="large"]') return sizes[0];
    if (selector === '[data-contrast="true"]') return contrasts[0];
    return null;
  },
};
function draw() {
  layouts = [newLayout]; sizes = [newSize]; contrasts = [newContrast]; active = {id: 'body'};
}
""" + _function(script, "layoutChanged") + "\n" + handlers + """
oldLayout.focus();
oldLayout.onkeydown({key: ' ', repeat: false, preventDefault() {}});
if (keyboardLayout !== 'fr' || active !== newLayout)
  throw Error('layout selection lost keyboard focus');
if (owner !== false || token !== '' || selected !== null)
  throw Error('a layout change away from Confirm did not start over');
oldSize.focus();
oldSize.onclick();
if (textSize !== 'large' || active !== newSize)
  throw Error('text-size selection lost keyboard focus');
oldContrast.focus();
oldContrast.onclick();
if (highContrast !== true || active !== newContrast)
  throw Error('contrast selection lost keyboard focus');
"""
    result = subprocess.run([node, "-e", program], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_text_size_utility_keeps_focus():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable")
    script = inline_script(gallery_html())
    # #175: text size is in Help & settings; the redraw keeps focus on it.
    start = script.index("let helpOpen = false")
    end = script.index("function renderHelpTrigger", start)
    handler = script[start:end]
    program = """
const P = {textSizes: [{id: 'standard', label: 'Standard'},
  {id: 'large', label: 'Large'}], textSizeUtility: 'Text size',
  sounds: {toggleOn: 'Sounds: on', toggleOff: 'Sounds: off'},
  helpMenu: {states: {owner: [{key: 'text_size', label: 'Text size: Standard', enabled: true, reason: ''}]}}};
let screen = 'owner', textSize = 'standard', soundsOn = false;
let keyboardFrom = null, reportHelpFrom = 'owner';
function draw() {}
""" + handler + """
openHelp();
activateHelp('text_size');
if (textSize !== 'large' || !helpOpen || helpFocus !== 'text_size')
  throw Error('text size did not keep the menu open on its item');
"""
    result = subprocess.run([node, "-e", program], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

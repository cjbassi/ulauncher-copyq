import html
import json
import logging
import subprocess
from shutil import which

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.ExtensionCustomAction import \
    ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import \
    RenderResultListAction
from ulauncher.api.shared.event import ItemEnterEvent, KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

logger = logging.getLogger(__name__)

if which("copyq") is None:
    raise Exception("'copyq' is not in $PATH.")

copyq_script_getAll = r"""
var result=[];
for ( var i = 0; i < size(); ++i ) {
    var obj = {};
    obj.row = i;
    obj.mimetypes = str(read("?", i)).split("\n");
    obj.mimetypes.pop();
    obj.text = str(read(i));
    result.push(obj);
}
JSON.stringify(result);
"""

copyq_script_getMatches = r"""
var result=[];
var match = "%s";
for ( var i = 0; i < size(); ++i ) {
    if (str(read(i)).search(new RegExp(match, "i")) !== -1) {
        var obj = {};
        obj.row = i;
        obj.mimetypes = str(read("?", i)).split("\n");
        obj.mimetypes.pop();
        obj.text = str(read(i));
        result.push(obj);
    }
}
JSON.stringify(result);
"""


class DemoExtension(Extension):

    def __init__(self):
        super(DemoExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        json_preferences = json.dumps(extension.preferences)
        logger.info(f'preferences {json_preferences}')

        query = event.get_argument()
        script = copyq_script_getAll
        script = copyq_script_getMatches % query if query else copyq_script_getAll
        proc = subprocess.check_output(
            ['copyq', '-'], input=script, encoding='utf8')
        json_arr = json.loads(proc)

        items = []
        for obj in json_arr:
            # item_name = html.escape(obj['text'].replace('\n', ' '))
            text = obj['text']
            item_name = html.escape(
                " ".join(filter(None, text.replace("\n", " ").split(" "))))

            # text = html.escape(" ".join(filter(None, text.replace("\n", " ").split(" "))))

            item_row = obj['row']
            item_types = ", ".join(obj['mimetypes'])
            data = {'row': item_row}
            items.append(
                ExtensionResultItem(icon='images/icon.png',
                                    name=item_name,
                                    description=f'{item_row}: {item_types}',
                                    on_enter=ExtensionCustomAction(
                                        data, keep_app_open=False)))

        return RenderResultListAction(items[:10])


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()
        row = data['row']
        subprocess.run(['copyq', f'select({row})'])


if __name__ == '__main__':
    DemoExtension().run()

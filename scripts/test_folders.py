import unittest
from unittest.mock import Mock
from tg_mcp import api
from tg_mcp.client import TelegramClient, TdlibError

# All folder names, IDs and chat responses below are synthetic test fixtures.
class FoldersTest(unittest.TestCase):
    def test_updates_empty_and_replacement(self):
        c=TelegramClient(1,'test',tdjson=Mock())
        with self.assertRaises(TimeoutError): c.get_chat_folders(0)
        c._handle_update({'@type':'updateChatFolders','chat_folders':[]})
        self.assertEqual(api.list_chat_folders(c)['folders'],[])
        c._handle_update({'@type':'updateChatFolders','chat_folders':[{'id':7,'name':{'text':{'text':'Example folder'}}}]})
        self.assertEqual(api.list_chat_folders(c)['folders'][0]['title'],'Example folder')
        snapshot=c.get_chat_folders(); snapshot['chat_folders'].clear()
        self.assertEqual(len(c.get_chat_folders()['chat_folders']),1)
    def test_partial_loading_and_paging(self):
        c=Mock(); c.get_chat_folders.return_value={'chat_folders':[{'id':7,'title':'Example folder'}]}
        loaded=[]
        def invoke(q):
            if q['@type']=='getChat': return {'id':q['chat_id'],'title':'chat'}
            self.assertEqual(q['chat_list'],{'@type':'chatListFolder','chat_folder_id':7})
            if q['@type']=='getChats': return {'chat_ids':loaded[:]}
            if len(loaded)==3: raise TdlibError(404,'done')
            loaded.append(len(loaded)+1); return {'@type':'ok'}
        c.invoke.side_effect=invoke
        self.assertEqual([x['id'] for x in api.list_chats(c,limit=5,offset=1,folder_id=7)],[2,3])
    def test_errors_not_hidden(self):
        c=Mock(); c.invoke.side_effect=[{'chat_ids':[]},TdlibError(429,'FLOOD_WAIT')]
        with self.assertRaises(TdlibError): api.list_chats(c)
    def test_unknown_folder_and_invalid_args(self):
        c=Mock(); c.get_chat_folders.return_value={'chat_folders':[]}
        for kwargs in ({'folder_id':42},{'limit':0},{'offset':-1},{'folder_id':7,'archived':True}):
            with self.assertRaises(ValueError): api.list_chats(c,**kwargs)
        c.invoke.assert_not_called()
    def test_main_archive(self):
        for archive,kind in [(False,'chatListMain'),(True,'chatListArchive')]:
            c=Mock(); c.invoke.return_value={'chat_ids':[1]}
            api.list_chats(c,limit=1,archived=archive)
            self.assertEqual(c.invoke.call_args_list[0].args[0]['chat_list']['@type'],kind)

if __name__=='__main__': unittest.main()

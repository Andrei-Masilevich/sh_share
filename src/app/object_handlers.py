from zipfile import ZipFile

import glob
import os
import yaml

from optparse import OptionValueError
import os.path as ps
from tornado2 import L

class CONFIG_YAML_FORMAT:
    OBJECTS = "objects"
    DEFAULT = "default"
    OBJECT_TYPE = "type"
    OBJECT_FOLDER = "folder"
    OBJECT_SYNONYMS = "synonyms"
    OBJECT_SYNONYM_ARCHIVE = "archive"
    OBJECT_SYNONYM_ENCRYPTED = "encrypted"
    OBJECT_SYNONYM_DATA = "data"
    OBJECT_SYNONYM_KEY = "key"


def init_objects(objects_file, source_folder, shadow):
    try:
        with open(objects_file, 'r') as f:
            parsed_yaml = yaml.safe_load(f)
            assert parsed_yaml, "Can't parse YAML"

            objects = parsed_yaml.get(CONFIG_YAML_FORMAT.OBJECTS)
            assert objects, "There is no %r key" % (CONFIG_YAML_FORMAT.OBJECTS)
            default_object = parsed_yaml.get(CONFIG_YAML_FORMAT.DEFAULT)
            for object_item in objects:
                for object_item_ in object_item.items():
                    (object_name, object_definition) = object_item_
                    break
                object_type = object_definition.get(CONFIG_YAML_FORMAT.OBJECT_TYPE)
                assert object_type, "There is no %r key" % (CONFIG_YAML_FORMAT.OBJECT_TYPE)
                object_type = object_type.upper()
                assert object_type in OBJECT_TYPES.keys(), "Not implemented type %r" % (object_type)
                
                object_synonyms = object_definition.get(CONFIG_YAML_FORMAT.OBJECT_SYNONYMS)
                if object_synonyms:
                    object_synonyms = list(object_synonyms)
                else:
                    object_synonyms = []
                synonyms = {}
                for object_synonym in object_synonyms:
                    for object_synonym_ in object_synonym.items():
                        (object_synonym_name, object_synonym_ext) = object_synonym_
                        synonyms[object_synonym_name] = object_synonym_ext
                        break
                folder = object_definition.get(CONFIG_YAML_FORMAT.OBJECT_FOLDER)
                if folder:
                    source_folder = ps.realpath(ps.join(source_folder, folder))
                assert ps.isdir(source_folder), "Invalid folder %r" % (source_folder)
                
                ObjectHandler.register_object("/".join([shadow, object_name]), 
                                                        OBJECT_TYPES.get(object_type), source_folder,
                                                        synonyms)
                if default_object and object_name == default_object:
                    ObjectHandler.register_object(shadow, 
                                                  OBJECT_TYPES.get(object_type), source_folder,
                                                  synonyms)
    except BaseException as err:
        raise AssertionError("Invalid %r: %s" % (objects_file, err))


class OPTIONS:
    MAX_PATH_DEPTH = 99
    BUFF_SIZE = 64 * 1024


class PingHandler(object):

    def __init__(self, request_handler):
        self.handler = request_handler

    def respose(self):
        self.handler.set_status(200, "OK")
        self.handler.finish()
    
    def do_HEAD(self):
        self.respose()

    def do_GET(self):
        self.respose()


class ZIPHandler(object):
    
    def __init__(self, request_handler, source_folder, object_path, synonyms):
        assert request_handler, "Invalid requiest handler"
        self.handler = request_handler
        assert any(object_path), "Invalid object path"
        self.object_name = object_path[0] 
        self.object_path = object_path[1:]
        self.source_folder = source_folder
        assert any(self.source_folder) and ps.isdir(source_folder), "Invalid source folder"
        self.synonyms = synonyms


    def find_file_object(self, name):
        if name == 'latest':
            files = glob.glob(ps.join(self.source_folder, "*.zip"))
            files.sort(key=ps.getmtime, reverse=True)
        else:
            if not name.endswith("zip"):
                name = f"{name}.zip"
            files = glob.glob(ps.join(self.source_folder, name))
        
        if any(files):
            return files[0]

        return None


    def send_file(self, f):
        while True:
            data = f.read(OPTIONS.BUFF_SIZE)
            if not data:
                break
            self.handler.write(data)


    def send_file_headers(self, description, filename, file_sz):
        self.handler.set_status(200, "OK")
        self.handler.set_header("Cache-Control", "max-age=0, must-revalidate")
        self.handler.set_header("Content-Description", description);
        self.handler.set_header("Content-Type", "application/octet-stream");
        self.handler.set_header("Content-Disposition", f"attachment; filename=\"{filename}\"");
        self.handler.set_header("Content-Transfer-Encoding", "binary");
        self.handler.set_header("Content-Length", str(file_sz));
        # TODO: it doesn't support pause for downloading now
        self.handler.set_header("Accept-Ranges", "none");

    def respose_zip(self, path, file_sz, header_only):
        assert file_sz > 0, "Empty file"
        
        filename = ps.basename(path)
        self.send_file_headers("zip", filename, file_sz)
        if not header_only:
            try:
                with open(path, 'rb') as f:
                    self.send_file(f)
            except OSError:
                return False
        self.handler.finish()
        return True

    def reponse_zip_item(self, path, item, header_only):
        try:
            with ZipFile(path) as archive:
                result_info = None
                synonym = self.synonyms.get(item)
                if synonym:
                    probs = []
                    for info in archive.infolist():
                        if info.filename.endswith(synonym):
                            probs.append(info)
                    if len(probs) > 1:
                        probs.sort(key=lambda info:info.date_time, reverse=True)
                    if any(probs):
                        result_info = probs[0]
                if not result_info:
                    result_info = archive.getinfo(item)
                self.send_file_headers(item, result_info.filename, result_info.file_size)
                if not header_only:
                    with archive.open(result_info.filename) as f:
                        self.send_file(f)
        except BaseException:
            return False
        self.handler.finish()
        return True

    def respose_not_found(self):
        self.handler.send_error(404)


    def respose(self, header_only = False):
        path = self.find_file_object(self.object_name)
        if path:
            file_sz = 0

            try:
                with open(path, 'rb') as f:
                    f.seek(0, os.SEEK_END)
                    file_sz = f.tell()
            except OSError:
                return None

            if file_sz < 1:
                return None
            
            if any(self.object_path):
                return self.reponse_zip_item(path, "/".join(self.object_path), header_only)
            else:
                return self.respose_zip(path, file_sz, header_only)
        else:
            return None
    
    def do_HEAD(self):
        if not self.respose(True):
            self.respose_not_found()
        
    def do_GET(self):
        if not self.respose():
            self.respose_not_found()


class ObjectHandler(object):

    object_handlers = {}
    
    @staticmethod
    def register_object(shadow, handler_class, folder, synonyms):
        assert any(shadow), "Empty shadow"
        assert any(folder) and ps.isdir(folder), "Invalid folder"
        
        object_type = shadow
        if object_type.startswith('/'):
            object_type = object_type[1:]
        ObjectHandler.object_handlers[object_type] = (handler_class, folder, synonyms)


    def __init__(self, request_handler):
        assert request_handler, "Invalid request handler"
        self.handler = request_handler


    def validate_path(self, input_path):
        for type_path in self.object_handlers.keys():
            if input_path == type_path or input_path.startswith(type_path + "/"):
                return type_path
        return None


    def route(self):
        input_path = self.handler.request.path[1:]
        object_type = self.validate_path(input_path)
        if not object_type:
            return None
        
        input_path = input_path[len(object_type):]
        object_path = input_path.split('/')
        
        if len(object_path) > OPTIONS.MAX_PATH_DEPTH:
            return None
        
        if not any(object_path):
            return PingHandler(self.handler)
        
        route = self.object_handlers.get(object_type)
        assert route, "Can't route"
        
        handler_class = route[0]
        source_folder = route[1]
        synonyms = route[2]
        return handler_class(self.handler, source_folder, object_path[1:], synonyms)


    def do_HEAD(self):
        router = self.route()
        if router:
            router.do_HEAD()
        else:
            self.handler.send_error(406)
        
        
    def do_GET(self):
        router = self.route()
        if router:
            router.do_GET()
        else:
            self.handler.send_error(406)
            

OBJECT_TYPES = {"ZIP": ZIPHandler}

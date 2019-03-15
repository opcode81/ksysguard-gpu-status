#!/usr/bin/env python3

# Ref: https://techbase.kde.org/Development/Tutorials/Sensors#Protocol

import subprocess
import xml.etree.ElementTree as ET
import collections

CmdInfo = collections.namedtuple('CmdInfo', ['current', 'min', 'max'])

zero = lambda _: 0

supported_query = {
    'Temperature(C)': CmdInfo(lambda gpu: gpu.find('./temperature/gpu_temp').text.split(' ')[0], zero, zero),
    'Utilization(%)': CmdInfo(lambda gpu: gpu.find('./utilization/gpu_util').text.split(' ')[0], zero, lambda _: 100),
    'Memory_Used(MiB)': CmdInfo(lambda gpu: gpu.find('./fb_memory_usage/used').text.split(' ')[0], zero, lambda gpu: gpu.find('./fb_memory_usage/total').text.split(' ')[0])}

def make_cmd(gpu_id, key):
    return f'{gpu_id}_{key}'

def break_cmd(cmd):
    return cmd.split('_', maxsplit=1)


class GPURenamer:
    def __init__(self):
        self.id2name = {}
        self.name2id = {}
        
    def name(self, identifier):
        name = self.id2name.get(identifier)
        if name is None:
            name = "GPU%d" % len(self.id2name)
            self.id2name[identifier] = name
            self.name2id[name] = identifier
        return name
    
    def identifier(self, name):
        return self.name2id[name]


if __name__ == '__main__':
    print('ksysguardd 1.2.0')
    keys = supported_query.keys()
    names_mapped = False
    renamer = GPURenamer()
    while True:
        cmd = input('ksysguardd> ')
        info = ET.fromstring(subprocess.check_output(['nvidia-smi', '-q', '-x']))
        if not names_mapped:
            names_mapped = True
            for gpu in info.findall('gpu'):
                renamer.name(gpu.attrib['id'])
        if cmd == 'monitors':
            for gpu in info.findall('gpu'):
                gpu_id = gpu.attrib['id']
                for key in keys:
                    print(f'{make_cmd(renamer.name(gpu_id), key)}\tfloat')
        else:
            gpu_name, key = break_cmd(cmd)
            gpu_id = renamer.identifier(gpu_name)
            gpu = info.find(f'.//gpu/[@id="{gpu_id}"]')
            if key.endswith('?'):
                cmd_info = supported_query[key[:-1]]
                print(f'{make_cmd(gpu_name, key[:-1])}\t{cmd_info.min(gpu)}\t{cmd_info.max(gpu)}')
            else:
                result = supported_query[key].current(gpu)
                print(result)

import time

import socket
import threading

import yaml
import ping3
from logzero import logger
import adbutils
import uiautomator2 as u2

# CONFIG BEGIN ----------
# 局域网 ip 如果为空则自动判断
LAN_IP = ""

# CONFIG END ----------
adb = adbutils.AdbClient(host="127.0.0.1", port=5037)


class AdbDevice:
    def __init__(self):
        try:
            with open("./devices.yaml", "r", encoding="utf-8") as f:
                self.devices = yaml.safe_load(f) or {}
        except (FileNotFoundError, yaml.parser.ParserError):
            self.devices = {}
        self.find_lan_devices()
        self.check_and_disconnect()
        self.update_device()

    def check_and_disconnect(self):
        """
        自动检测是否需要连接的设备
        :return:
        """
        for _device in adb.device_list():
            if _device.prop.get("ro.serialno") in self.devices:
                if not self.devices[_device.prop.get("ro.serialno")]["enable"]:
                    logger.debug(
                        f'{_device.serial}:{_device.prop.get("ro.product.name")} enable为`false` 已排除')
                    adb.disconnect(_device.serial)

    def update_device(self):
        for _device in adb.device_list():
            logger.debug(
                f'{_device.serial}:{_device.prop.get("ro.product.name")}:{self.devices[_device.prop.get("ro.serialno")].get("alias")} 连接成功')
            try:
                _device_ip = _device.wlan_ip()
            except IndexError:
                _device_ip = None
            self.devices[_device.prop.get("ro.serialno")] = {"name": _device.prop.get("ro.product.name"),
                                                             "manufacturer": _device.prop.get(
                                                                 "ro.product.manufacturer"),
                                                             "brand": _device.prop.get("ro.product.brand"),
                                                             "version": _device.prop.get("ro.build.version.release"),
                                                             "ip": _device_ip,
                                                             "width": _device.window_size().width,
                                                             "height": _device.window_size().height,
                                                             }
            self.devices[_device.prop.get("ro.serialno")]["alias"] = self.devices[_device.prop.get("ro.serialno")].get(
                "alias") or ""
            self.devices[_device.prop.get("ro.serialno")]["enable"] = self.devices[_device.prop.get("ro.serialno")].get(
                "enable") or True
            # print(self.devices[_device.prop.get("ro.serialno")])
        with open("./devices.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(self.devices, f)

    @staticmethod
    def find_lan_devices():
        """
        自动连接上局域网所有的安卓设备
        :return:
        """

        def is_connect(address):
            if ping3.ping(address):
                adb.connect(address)

        lan_ip = (LAN_IP or socket.gethostbyname_ex(socket.gethostname())[-1][-1]).split(".")
        gateway = lan_ip[:3]
        # 依此尝试连接
        for _ in range(256):
            target_ip = ".".join(gateway) + "." + str(_)
            threading.Thread(target=is_connect, args=(target_ip,)).start()
        time.sleep(5)


a = AdbDevice()

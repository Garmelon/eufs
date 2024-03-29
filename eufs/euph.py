import json
import threading
import time

import websockets.sync.client as ws


class Message:
    def __init__(self, info):
        mid = info["id"]
        mparent = info.get("parent")
        mtime = info["time"]
        mnick = info["sender"]["name"]
        mcontent = info["content"]

        self.id = mid
        self.parent = mparent
        self.time = mtime
        self.text = f"[{mnick}] {mcontent}"
        self.children = {}  # id -> msg

        self.text = self.text.replace("/", "?")[:50]
        print(mid, mparent)


def find_msg_by_text(msgs, text):
    for msg in msgs.values():
        if msg.text == text:
            return msg


class Room:
    def __init__(self, name):
        self.name = name

        self.ws = None
        self.alive = True
        self.next_id = 0

        self.nick = ""
        self.msgs = {}  # id -> msg

    def start(self):
        t = threading.Thread(target=Room._run, args=(self,), daemon=True)
        t.start()

    def stop(self):
        self.alive = False
        self.ws.close()

    def send(self, content, parent=None):
        self._send("send", content=content, parent=parent)

    def find_msg_by_texts(self, texts):
        msg = None
        children = {mid: msg for mid, msg in self.msgs.items() if msg.parent == None}

        for text in texts:
            msg = find_msg_by_text(children, text)
            if not msg:
                return
            children = msg.children

        return msg

    def _run(self):
        while self.alive:
            self.ws = ws.connect(f"wss://euphoria.leet.nu/room/{self.name}/ws")

            try:
                while True:
                    packet = self.ws.recv()
                    packet = json.loads(packet)
                    self._on_packet(packet)
            except Exception as e:
                print("Oop:", e)
                if self.alive:
                    print("Disconnected or something, waiting before reconnecting")
                    time.sleep(10)

        print("Stopped")

    def _send(self, ptype, **data):
        cur_ws = self.ws
        if cur_ws is None:
            return

        pid = f"{self.next_id}"
        self.next_id += 1

        packet = {
            "id": pid,
            "type": ptype,
            "data": data,
        }
        packet = json.dumps(packet)
        cur_ws.send(packet)

    def _on_packet(self, packet):
        data = packet.get("data", {})

        match packet["type"]:
            case "ping-event":
                self._on_ping_event(data)
            case "hello-event":
                self._on_hello_event(data)
            case "snapshot-event":
                self._on_snapshot_event(data)
            case "send-event":
                self._on_send_event(data)
            case "send-reply":
                self._on_send_event(data)

        print(packet["type"])

    def _on_ping_event(self, data):
        self._send("ping-reply", time=data["time"])

    def _on_hello_event(self, data):
        self.nick = data["session"]["name"]

    def _on_snapshot_event(self, data):
        self.nick = data.get("nick", self.nick)

        # Load messages
        for msg in data["log"]:
            msg = Message(msg)
            self.msgs[msg.id] = msg

        # Fill in message children
        for msg in self.msgs.values():
            if msg.parent is not None:
                parent = self.msgs.get(msg.parent)
                if parent is not None:
                    parent.children[msg.id] = msg

        self._send("nick", name="garmtest")

    def _on_send_event(self, data):
        msg = Message(data)
        self.msgs[msg.id] = msg

        if msg.parent is not None:
            parent = self.msgs.get(msg.parent)
            if parent is not None:
                parent.children[msg.id] = msg

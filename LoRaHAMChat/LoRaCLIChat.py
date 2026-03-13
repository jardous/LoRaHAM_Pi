#!/usr/bin/env python3
#
# Benötigt:
# pip install termcolor

import time
import threading
import base64
import binascii
from termcolor import colored

from SX127x.LoRa import LoRa, MODE, BW, CODING_RATE
from SX127x.board_config import BOARD

# English:
# Here you can add APRS-specific information.
# This turns it into a real chat.
# Change "ALL" to a target callsign such as DC2WA to address the recipient directly. 
# You can then type messages directly and send them with the enter key. The appropriate APRS header will then be added

# Deutsch:
# Hier kannst du APRS-Spezifische Infos hinzufügen.
# Dadurch wird es zu einemechten Chat.
# Ändere "ALL" zu einem Zielrufzeichen wie z.B. DC2WA um den Empfänger direkt zu adressieren. 
# Du kannst dann direkt Nachrichten tippen und mit eingabetaste versenden. Der passende APRS-Header wird dann hinzugefügt

# Text, den du hinzufügen möchtest
mein_text = "DC2WA>APRS,WIDE1-1::ALL      :"
#mein_text = "DC2WA>APRS,WIDE1-1::DF2FK    :"
#mein_text = "DC2WA>APRS,WIDE1-1::DC2WA-15 :"
#mein_text = "DC2WA>APRS,WIDE1-1::DB0ARD-10:"
my_code = "J5150"

my_text = my_code + ">APRS,WIDE1-1::ALL      :"

BOARD.setup()
BOARD.reset()

SEND_FREQ = 433.775  # Sendefrequenz in MHz
RECV_FREQ = 433.900  # Empfangsfrequenz in MHz
BW = BW.BW125  # Bandbreite
CODING_RATE = CODING_RATE.CR4_5  # Codierungsrate
SPREADING_FACTOR = 12  # Spreizfaktor

MESSAGES_FILE = "messages433.txt"


class LoRaSender(LoRa):
    def __init__(self, verbose=False):
        super(LoRaSender, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        self.set_freq(RECV_FREQ)
        self.set_mode(MODE.RXCONT)

    def on_rx_done(self):
        payload = self.read_payload(nocheck=True)
        self.clear_irq_flags(RxDone=1)
        self.reset_ptr_rx()
 
        print("Received:", binascii.hexlify(payload))
        try:
            from lorawan.lorawan import LorawanMAC
            lorawan = LorawanMAC()
            lorawan.read(payload)
            print("loravan: %s", lorawan)
        except:
            print("can't decode lorawan")
        message = repr(bytes(payload))[2:-1]
        print(colored(f"received", "red") + colored(message, "cyan"))

        time.sleep(0.2)
        self.set_mode(MODE.RXCONT)

        self.save_message(message, 'received')
        print("> ", end=" ")

    def send_message(self, message):
        self.set_mode(MODE.SLEEP)
        self.set_freq(SEND_FREQ)
        
        prefix = [ord('<'), 255, 1]
        prefix.extend([ord(char) for char in my_text])
        payload = prefix + [ord(c) for c in message]
        print(colored("", "white") + colored(my_text+message, "yellow")) # colored(zentrierter_text, 'white', 'on_blue')
        
        self.write_payload(payload)
        self.set_mode(MODE.TX)
        time.sleep(0.2)
        
        self.set_mode(MODE.SLEEP)
        self.set_freq(RECV_FREQ)
        self.set_mode(MODE.RXCONT)


    def on_cad_done(self):
        print("\non_CadDone")
        print(self.get_irq_flags())

    def start_receiving(self):
        """Startet eine Schleife, um dauerhaft Nachrichten zu empfangen."""
        while True:
            self.set_mode(MODE.RXCONT)
            time.sleep(0.1)


if __name__ == "__main__":

    lora = LoRaSender(verbose=True)
    lora.set_pa_config(pa_select=1, max_power=21, output_power=20)
    lora.set_bw(BW)
    lora.set_coding_rate(CODING_RATE)
    lora.set_spreading_factor(SPREADING_FACTOR)
    
    lora.set_rx_crc(True)
    lora.set_low_data_rate_optim(True)

    # Starte den Empfangs-Thread
    recv_thread = threading.Thread(target=lora.start_receiving, daemon=True)
    recv_thread.start()

    while True:
        message = input(colored("> ", "yellow"))
        if message.lower() == 'exit':
            print("Chat wird beendet...")
            break
        lora.send_message(message)
        
        time.sleep(1)


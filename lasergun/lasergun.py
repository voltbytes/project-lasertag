from machine import Pin
from utime import sleep_ms
from micropython import schedule
import _thread

#Code made for RP2040 microcontrollers. If running on different platform changes may be required.

class lasergun():
    def __init__(self, laserpin, triggerpin, modepin, reloadpin, ooapin):
        self.laserpin = Pin(laserpin, Pin.OUT) #the Pin connected to the laser head through transistor
        self.cycledelay = 100 #the standard delay in ms for a new round to cycle, limits rate of fire on rapidfiring
        self.triggerpin = Pin(triggerpin, Pin.IN, Pin.PULL_DOWN) #connected to tactile switch
        self.triggerpin.irq(handler=self.pulldown_trigger, trigger=Pin.IRQ_RISING)
        self.modes = {1:"single", 2:"burst", 3:"full"}
        self.mode = 1
        self.modepin = Pin(modepin, Pin.IN, Pin.PULL_DOWN) #connnected to tactile switch
        self.modepin.irq(handler=self.flick_switch, trigger=Pin.IRQ_RISING)
        self.switch_mode = self.switchmode #initialization for scheduling
        self.ammocap = 21
        self.rounds_loaded = self.ammocap
        self.consume_round = self.consumeround #initialization for scheduling
        self.reloadpin = Pin(reloadpin, Pin.IN, Pin.PULL_DOWN) #connected to tactile switch
        self.reloadpin.irq(handler=self.reload, trigger=Pin.IRQ_RISING)
        self.reload_mag = self.reloadmag #initialization for scheduling
        self.reloaddelay = 1000
        self.ooapin = Pin(ooapin, Pin.OUT)
        
    def pulldown_trigger(self, irq=None):
        """IRQ-triggered function, determines firing based on current mode"""
        print("Trigger pressed")
        if self.modes[self.mode]=="single":
            if self.rounds_loaded>0:
                self.fire()
        elif self.modes[self.mode]=="burst":
            for i in range(0,3):
                if self.triggerpin.value()==1 and self.rounds_loaded>0:
                    self.fire()
                else:
                    break
        elif self.modes[self.mode]=="full":
            while self.triggerpin.value()==1 and self.rounds_loaded>0:
                self.fire()
        if self.rounds_loaded==0:
            self.ooapin.on()
            print("Out of Ammo")
                
    def fire(self):
        """Indirectly IRQ-triggered through above function, handles firing
        Additionally schedules the round-consuming function"""
        self.laserpin.on()
        #schedule(self.consume_round,None) #intense pressing caused RuntimeError: Schedule queue full
        _thread.start_new_thread(self.consume_round, ()) #Assigning consumption to other thread works fine instead
        sleep_ms(100) #this not only makes laser blinking visible but ensures _thread exits before a new one is initialized
        self.laserpin.off()
        sleep_ms(self.cycledelay)
        
    def flick_switch(self, irq=None):
        """IRQ-triggered function, schedules the mode-switching function"""
        schedule(self.switch_mode,None)
        
    def switchmode(self, args=None):
        """Handles mode switching, schedulable function"""
        if self.mode == len(self.modes): #if mode was on last one, reset to first, else just increase by one
            self.mode = 1
        else:
            self.mode += 1
        print("Mode:"+self.modes[self.mode])
        
    def consumeround(self, args=None):
        """Handles round consumption, schedulable function"""
        if self.rounds_loaded > 0:
            self.rounds_loaded -= 1
            print("Ammo left: "+str(self.rounds_loaded))
            
    def reloadmag(self, args=None):
        """Handles reloading, schedulable function"""
        if self.triggerpin.value() == 0:
            self.rounds_loaded = self.ammocap
            print("Reloaded: "+str(self.rounds_loaded))
            self.ooapin.off()
        else:
            print("Cannot reload while firing")
            
    def reload(self, irq=None):
        """IRQ-triggered function, enforces reload-delay for testing purposes
        Also schedules the ammo-reloading function"""
        sleep_ms(self.reloaddelay)
        schedule(self.reload_mag,None)

if __name__=='__main__':        
    l = lasergun(0,1,2,3,4)
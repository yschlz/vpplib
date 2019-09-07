# -*- coding: utf-8 -*-
"""
Created on Thu May  2 12:13:59 2019

@author: patri
"""


import numpy as np
import pandas as pd
from gym import spaces
import gym
from collections import deque
from model.VPPPhotovoltaic import VPPPhotovoltaic
from model.VPPEnergyStorage import VPPEnergyStorage
from model.VPPHousehold import VPPHousehold

class ems(gym.Env):
               
    """
        Info
        ----
        The ems-class is the training environment for the DDQN-Agent. 
        
        Parameters
        ----------
        Under __init__ 
        ...
        	
        Attributes
        ----------
        
        ...
        
        Notes
        -----
        The offset variable takes into account that there are nearly no days with more PV-production than electricity demand. 
        ...
        
        References
        ----------
        
        ...
        
        Returns
        -------
        
        ...
        
    """

    def __init__(self, EP_LEN):
        super(ems, self).__init__()
        self.LOG_EVENTS = False
        self.EP_LEN = EP_LEN
        self.obs = 3
        self.offset = 24 * 4 * 7 * 13 
        self.observation_space = spaces.Box(low=0, high=1, shape = (self.obs,), dtype=np.float32)
        self.action_space = spaces.Discrete(3)
        self.time = 0 + self.offset
        self.residual = 0
        self.max_pv = 0
        self.r = 0
        self.log = deque(maxlen=self.EP_LEN)
        self.el_storage = VPPEnergyStorage(15, 25, 0.9, 0.9, 5, 1)
        self.pv = self.prepareTimeSeriesPV()
        self.el_storage.prepareTimeSeries()
        self.loadprofile = VPPHousehold(15, None, None)
        self.max = max(self.loadprofile.data)
        
        
    def prepareTimeSeriesPV(self):
        """
        Info
        ----
        This method initializes the PV-Lib module with its necessary parameters.
        
        Parameters
        ----------
        
        ...
        	
        Attributes
        ----------
        
        ...
        
        Notes
        -----
        
        ...
        
        References
        ----------
        
        ...
        
        Returns
        -------
        A DataFrame Object with the 
        ...
        
        """
        latitude = 50.941357
        longitude = 6.958307
        name = 'Cologne'
        
        weather_data = pd.read_csv("./Input_House/PV/2017_irradiation_15min.csv")
        weather_data.set_index("index", inplace = True)
        
        pv = VPPPhotovoltaic(timebase=15, identifier=name, latitude=latitude, longitude=longitude, modules_per_string=5, strings_per_inverter=1)
        pv.prepareTimeSeries(weather_data)
        return pv
        
    def reset(self):
        """
        Info
        ----
        This method resets all necessary parameters for a new episode of the training.
        
        Parameters
        ----------
        
        ...
        	
        Attributes
        ----------
        
        ...
        
        Notes
        -----
        
        ...
        
        References
        ----------
        
        ...
        
        Returns
        -------
        The starting state as an array of zeros, as the first observation for the agent.
        ...
        
        """
        self.rand_start = int(np.random.rand()*25000)+self.offset
        state = np.array(np.zeros(self.obs))
        self.time = self.rand_start
        self.residual = 0       
        self.cum_r = 0
        self.el_storage.stateOfCharge = 0
        return state

    def step(self, action):
        """
        Info
        ----
        This method performs a step through the environment.
        
        Parameters
        ----------
        
        ...
        	
        Attributes
        ----------
        
        ...
        
        Notes
        -----
        0 = nichts
        1 = Laden
        2 = Entladen  
        ...
        
        References
        ----------
        
        ...
        
        Returns
        -------
        The current state of necessary observations as an array.
        ...
        
        """      
        #action = self.best_policy()
        r, is_valid_action = -1, False
        #Action 0: Nichts
        if action == 0: r, is_valid_action = 0, True
        #Action 1: Laden
        if action == 1 and self.residual < 0:
            r = 1#abs(self.residual)*10
            is_valid_action = self.el_storage.charge(abs(self.residual), 15, self.time)
        #Action 2: Entladen
        if action == 2 and self.residual > 0:
            r = 1#abs(self.residual)*10
            is_valid_action = self.el_storage.discharge(abs(self.residual), 15, self.time)
        #Fehler- und Rewardüberprüfung
        if not is_valid_action: r = -1 
        #Bereite den nächsten state vor
        self.residual = self.loadprofile.valueForTimestamp(self.time) - self.pv.valueForTimestamp(self.time)*10
        res_bool = self.residual > 0     
        state = np.array([np.round(self.el_storage.stateOfCharge/self.el_storage.capacity, 2), self.residual/self.max, res_bool])
        self.time += 1
        done = self.time >= self.rand_start + self.EP_LEN

        return state, r, done, self.cum_r
    
    def best_policy(self):
        if (self.el_storage.stateOfCharge == 0 and self.residual > 0) or (self.el_storage.stateOfCharge == 1 and self.residual < 0):
            return 0
        
        if self.el_storage.stateOfCharge != 1 and self.residual < 0:
            return 1
        
        if self.el_storage.stateOfCharge != 0 and self.residual > 0:
            return 2
        
        return print(self.el_storage.stateOfCharge, self.residual)
import itertools

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import resnet18
import numpy as np


class GRU(nn.Module):
    def __init__(self):
        super().__init__()
        self.hidden_size = 1024
        self.gru = nn.GRUCell(input_size=1024+128, hidden_size=self.hidden_size)

    def forward(self, x, h):
        x = self.gru(x, h)
        return x



class Kinect(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(*list(resnet18(pretrained=True).children())[:-1])
        for params in self.network.parameters():
            params.requires_grad = False


    def forward(self, x):
        x = self.network(x)
        return x.reshape(x.shape[0], -1)


class Video(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(*list(resnet18(pretrained=True).children())[:-1])
        for params in self.network.parameters():
            params.requires_grad = False

    def forward(self, x):
        x = self.network(x)
        return x.reshape(x.shape[0], -1)



class Audio(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Conv2d(kernel_size=4, padding=0, in_channels=1, out_channels=16, stride=2, bias=1),
            nn.ReLU(),
            nn.BatchNorm2d(num_features=16),
            nn.MaxPool2d(kernel_size=2),
            nn.Conv2d(kernel_size=4, padding=0, in_channels=16, out_channels=8, bias=1),
            nn.ReLU(),
            nn.BatchNorm2d(num_features=8),
            nn.MaxPool2d(kernel_size=2))
        self.linear = nn.Linear(in_features=2288, out_features=128)
        self.linear.requires_grad=False

    def forward(self, x):
        x = self.network(x)
        x = self.linear(x.reshape(x.shape[0], -1))
        x = F.relu(x)
        return x


class Classifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.video = Video()
        self.gru = GRU()
        self.audio = Audio()
        self.kinect = Kinect()
        self.linear = nn.Linear(in_features=1024, out_features=7)
        self.combo = list(itertools.product([i for i in range(40)],[i for i in range(20)]))

    def forward(self, audio, video_arr, motion_arr):
        if torch.cuda.is_available():
            h = torch.zeros((video_arr.shape[0], self.gru.hidden_size)).cuda()
        else:
            h = torch.zeros((video_arr.shape[0], self.gru.hidden_size))
        audio = self.audio(audio)
        for i in range(motion_arr.shape[1]*2):
            if np.random.uniform(0,1) > 0.5:
                j,k = self.combo[np.random.randint(0, len(self.combo)-1)]
                video_seq = self.video(video_arr[:, k, :, :])
                kinect_seq = self.kinect(motion_arr[:, j, :, :].transpose(1,3))
            else:
                video_seq = self.video(video_arr[:, int(i / 4), :, :])
                kinect_seq = self.kinect(motion_arr[:, int(i/2), :, :].transpose(1,3))
            x = torch.cat([audio, video_seq, kinect_seq], dim=1)
            h = self.gru(x, h)

        x = self.linear(h)
        return x

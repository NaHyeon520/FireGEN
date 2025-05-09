import torch
import torch.nn as nn
from torch.nn.functional import relu, sigmoid
import torch.nn.functional as F

class MHSA(nn.Module):
    def __init__(self, in_channels, num_heads=8):
        super().__init__()
        # 임베딩 차원(in_channels)이 num_heads로 나누어져야 합니다.
        assert in_channels % num_heads == 0, "in_channels must be divisible by num_heads"
        self.in_channels = in_channels
        self.num_heads = num_heads
        # PyTorch의 MultiheadAttention: embed_dim, num_heads
        # 여기서는 query/key/value 모두 in_channels 차원을 가집니다.
        self.mha = nn.MultiheadAttention(embed_dim=in_channels, 
                                         num_heads=num_heads,
                                         batch_first=True)
        # 학습 가능한 스케일 파라미터
        self.gamma = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        """
        x: (B, C, H, W)
        returns: (B, C, H, W) — 입력 x와 동일한 크기
        """
        B, C, H, W = x.shape
        # 1) (B, C, H, W) → (B, H*W, C)
        tokens = x.view(B, C, H*W).permute(0, 2, 1)

        # 2) Self-Attention: query, key, value 모두 tokens
        #    반환값: attn_output (B, H*W, C), attn_weights (B, H*W, H*W)
        attn_output, _ = self.mha(tokens, tokens, tokens)

        # 3) 다시 (B, C, H, W)로 복원
        attn_output = attn_output.permute(0, 2, 1).view(B, C, H, W)

        # 4) 스케일 조정 후 Residual 연결
        return self.gamma * attn_output + x


class Generator(nn.Module):
    def __init__(self, input_channels=12, kernel_size=2, stride=1, padding=1, dropout_rate=0.5):
        super().__init__()

        # Encoder Blocks
        self.e1 = nn.Conv2d(input_channels, 32, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.lr1 = nn.LeakyReLU(0.2, inplace=False)

        self.e2 = nn.Conv2d(32, 64, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.eb2 = nn.BatchNorm2d(64)
        self.lr2 = nn.LeakyReLU(0.2, inplace=False)

        self.e3 = nn.Conv2d(64, 128, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.eb3 = nn.BatchNorm2d(128)
        self.lr3 = nn.LeakyReLU(0.2, inplace=False)

        self.e4 = nn.Conv2d(128, 256, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.eb4 = nn.BatchNorm2d(256)
        self.lr4 = nn.LeakyReLU(0.2, inplace=False)

        #self.e5 = nn.Conv2d(512, 512, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        #self.eb5 = nn.BatchNorm2d(512)
        #self.lr5 = nn.LeakyReLU(0.2, inplace=False)

        self.mhsa = MHSA(in_channels=256, num_heads=8)

        # self.e6 = nn.Conv2d(512, 512, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        # self.eb6 = nn.BatchNorm2d(512)
        # self.lr6 = nn.LeakyReLU(0.2, inplace=False)

        # self.e7 = nn.Conv2d(512, 512, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        # self.eb7 = nn.BatchNorm2d(512)
        # self.lr7 = nn.LeakyReLU(0.2, inplace=False)

        # self.e8 = nn.Conv2d(512, 512, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        # self.eb8 = nn.BatchNorm2d(512)
        # self.lr8 = nn.LeakyReLU(0.2, inplace=False)

        # # Decoder Blocks
        # self.upconv1 = nn.ConvTranspose2d(512, 512, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        # self.db1 = nn.BatchNorm2d(512)
        # self.do1 = nn.Dropout(dropout_rate)

        # self.upconv2 = nn.ConvTranspose2d(512, 512, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        # self.db2 = nn.BatchNorm2d(512)
        # self.do2 = nn.Dropout(dropout_rate)

        # self.upconv3 = nn.ConvTranspose2d(512, 512, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        # self.db3 = nn.BatchNorm2d(512)
        # self.do3 = nn.Dropout(dropout_rate)

        #self.upconv4 = nn.ConvTranspose2d(512, 512, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        #self.db4 = nn.BatchNorm2d(1024)
        #self.do4 = nn.Dropout(dropout_rate)

        self.upconv5 = nn.ConvTranspose2d(256, 128, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.db5 = nn.BatchNorm2d(256)

        self.upconv6 = nn.ConvTranspose2d(256, 64, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.db6 = nn.BatchNorm2d(128)

        self.upconv7 = nn.ConvTranspose2d(128, 32, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.db7 = nn.BatchNorm2d(64)

        # Output
        #self.output = nn.Conv2d(128, 1, kernel_size=1, stride=1, padding=0)
        self.output = nn.ConvTranspose2d(64, 1, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)


    def forward(self, x):
        # Encoder
        e1 = self.e1(x)
        lr1 = self.lr1(e1)

        e2 = self.e2(lr1)
        eb2 = self.eb2(e2)
        lr2 = self.lr2(eb2)

        e3 = self.e3(lr2)
        eb3 = self.eb3(e3)
        lr3 = self.lr3(eb3)

        e4 = self.e4(lr3)
        eb4 = self.eb4(e4)
        lr4 = self.lr4(eb4)

        #e5 = self.e5(lr4)
        #eb5 = self.eb5(e5)
        #lr5 = self.lr5(eb5)

        # e5 = (B, 512, H, W) — bottleneck 출력
        e5_attn = self.mhsa(e4)

        # e6 = self.e6(lr5)
        # eb6 = self.eb6(e6)
        # lr6 = self.lr6(eb6)

        # e7 = self.e7(lr6)
        # eb7 = self.eb7(e7)
        # lr7 = self.lr7(eb7)

        # e8 = self.e8(lr7)
        # eb8 = self.eb8(e8)
        # lr8 = self.lr8(eb8)

        # # Decoder
        # upconv1 = self.upconv1(lr8)
        # upconv1 = torch.cat([upconv1, e7], dim=1)
        # db1 = self.db1(upconv1)
        # do1 = self.do1(db1)
        # d1 = relu(do1)
        # print('9')
        # upconv2 = self.upconv2(d1)
        # upconv2 = torch.cat([upconv2, e6], dim=1)
        # db2 = self.db2(upconv2)
        # do2 = self.do2(db2)
        # d2 = relu(do2)

        # upconv3 = self.upconv3(lr5)
        # upconv3 = torch.cat([upconv3, e5], dim=1)
        # db3 = self.db1(upconv3)
        # do3 = self.do1(db3)
        # d3 = relu(do3)

        #upconv4 = self.upconv4(lr5) # WAS d3
        #upconv4 = self.upconv4(e5_attn) 
        #upconv4 = torch.cat([upconv4, e4], dim=1)
        #db4 = self.db4(upconv4)
        #do4 = self.do4(db4) # ADDED THIS
        #d4 = relu(do4)

        upconv5 = self.upconv5(lr4)
        upconv5 = torch.cat([upconv5, e3], dim=1)
        db5 = self.db5(upconv5)
        d5 = relu(db5)

        upconv6 = self.upconv6(d5)
        upconv6 = torch.cat([upconv6, e2], dim=1)
        db6 = self.db6(upconv6)
        d6 = relu(db6)

        upconv7 = self.upconv7(d6)
        upconv7 = torch.cat([upconv7, e1], dim=1)
        db7 = self.db7(upconv7)
        d7 = relu(db7)

        

        # Use sigmoid 
        out = self.output(d7)
        out = sigmoid(out)

        return out

    
class Discriminator(nn.Module):
    def __init__(self, input_channels=13, kernel_size=4, stride=2, padding=1):
        super().__init__()

        self.e1 = nn.Conv2d(input_channels, 64, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.lr1 = nn.LeakyReLU(0.2, inplace=False)

        self.e2 = nn.Conv2d(64, 128, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.eb2 = nn.BatchNorm2d(128)
        self.lr2 = nn.LeakyReLU(0.2, inplace=False)

        self.e3 = nn.Conv2d(128, 256, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        self.eb3 = nn.BatchNorm2d(256)
        self.lr3 = nn.LeakyReLU(0.2, inplace=False)

        #self.e4 = nn.Conv2d(256, 512, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        #self.eb4 = nn.BatchNorm2d(512)
        #self.lr4 = nn.LeakyReLU(0.2, inplace=False)

        # Output
        #self.output = nn.Conv2d(512, 1, kernel_size=4, stride=1, padding=1)
        self.output = nn.Conv2d(256, 1, kernel_size=4, stride=1, padding=1)

    
    def forward(self, input, target):
        x = torch.cat([input, target], dim=1)
        e1 = self.e1(x)
        lr1 = self.lr1(e1)
        e2 = self.e2(lr1)
        eb2 = self.eb2(e2)
        lr2 = self.lr2(eb2)
        e3 = self.e3(lr2)
        eb3 = self.eb3(e3)
        lr3 = self.lr3(eb3)
        #e4 = self.e4(lr3)
        #eb4 = self.eb4(e4)
        #lr4 = self.lr4(eb4)
        out = self.output(lr3)

        return out
        
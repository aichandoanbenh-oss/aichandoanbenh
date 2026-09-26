"""Build only explicitly supported checkpoint architectures."""
from torch import nn
from torchvision import models

def from_checkpoint(checkpoint):
    architecture=checkpoint.get('architecture','resnet18')
    if architecture=='resnet18':
        model=models.resnet18(weights=None)
        model.fc=nn.Linear(model.fc.in_features,len(checkpoint['classes']))
    elif architecture=='efficientnet_b0':
        model=models.efficientnet_b0(weights=None)
        model.classifier[1]=nn.Linear(model.classifier[1].in_features,len(checkpoint['classes']))
    else:
        raise ValueError('Unsupported architecture: '+architecture)
    model.load_state_dict(checkpoint['state_dict'])
    return model.eval()

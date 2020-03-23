from model import Classifier
import torch
from trainer import Trainer
from torch.utils.data import DataLoader
import torch.optim as optim


def run(config, train_dataset, val_dataset):
    model = Classifier()

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=config['lr'])

    train_loader = DataLoader(train_dataset, batch_size=config['batch_size'], drop_last=True, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config['batch_size'], drop_last=True, shuffle=True)

    trainer = Trainer(model, train_loader, val_loader, criterion, optimizer, config, device)
    train_acc, train_loss, val_acc, val_loss = trainer.train()
    return train_acc, train_loss, val_acc, val_loss

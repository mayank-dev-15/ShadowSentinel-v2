import os
import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from .lstm_autoencoder import LSTMAnomalyDetector


def load_flow_data(path):
    data = []
    labels = []
    with open(path, 'r') as f:
        for line in f:
            record = json.loads(line)
            features = record.get('features', [])
            label = record.get('label', 0)
            data.append(features)
            labels.append(label)
    return np.array(data, dtype=np.float32), np.array(labels, dtype=np.float32)


class FlowDataset(TensorDataset):
    def __init__(self, features):
        self.tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(1)

    def __len__(self):
        return len(self.tensor)

    def __getitem__(self, idx):
        return self.tensor[idx], self.tensor[idx]


def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    for batch_x, batch_y in loader:
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        optimizer.zero_grad()
        output = model(batch_x)
        loss = criterion(output, batch_y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)


def train(config):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    data_path = config.get('data_path', 'data/flow_train.jsonl')
    features_dim = config.get('input_dim', 28)
    batch_size = config.get('batch_size', 64)
    epochs = config.get('epochs', 50)
    lr = config.get('learning_rate', 1e-3)
    save_path = config.get('save_path', 'models/saved/lstm_ae.pt')

    try:
        X, _ = load_flow_data(data_path)
    except FileNotFoundError:
        print(f"Training data not found at {data_path}. Creating synthetic data for demo.")
        X = np.random.randn(5000, features_dim).astype(np.float32)

    dataset = FlowDataset(X)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = LSTMAnomalyDetector(input_dim=features_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    for epoch in range(epochs):
        loss = train_epoch(model, loader, optimizer, criterion, device)
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} - Loss: {loss:.6f}")
            validate(model, loader, device)

    os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
    torch.save(model.state_dict(), save_path)
    print(f"Model saved to {save_path}")
    return model


def validate(model, loader, device):
    model.eval()
    total_loss = 0
    criterion = nn.MSELoss()
    with torch.no_grad():
        for batch_x, batch_y in loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            output = model(batch_x)
            loss = criterion(output, batch_y)
            total_loss += loss.item()
    avg_loss = total_loss / len(loader)
    print(f"  Validation loss: {avg_loss:.6f}")
    return avg_loss


def predict(model, features, device=None):
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.eval()
    model.to(device)
    tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)
    with torch.no_grad():
        recon = model(tensor)
        loss = nn.MSELoss(reduction='none')(recon, tensor)
        score = loss.mean().item()
    return score


if __name__ == '__main__':
    config = {
        'data_path': 'data/flow_train.jsonl',
        'input_dim': 28,
        'batch_size': 64,
        'epochs': 50,
        'learning_rate': 1e-3,
        'save_path': 'models/saved/lstm_ae.pt',
    }
    train(config)

import torch
import torch.nn as nn


class LSTMEncoder(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2 if num_layers > 1 else 0)
        self.fc = nn.Linear(hidden_dim, hidden_dim // 2)

    def forward(self, x):
        out, (h_n, c_n) = self.lstm(x)
        hidden = h_n[-1]
        encoded = self.fc(hidden)
        return encoded


class LSTMDecoder(nn.Module):
    def __init__(self, encoded_dim, hidden_dim, output_dim, seq_len, num_layers=2):
        super().__init__()
        self.seq_len = seq_len
        self.fc = nn.Linear(encoded_dim, hidden_dim)
        self.lstm = nn.LSTM(hidden_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2 if num_layers > 1 else 0)
        self.output = nn.Linear(hidden_dim, output_dim)

    def forward(self, z):
        x = self.fc(z).unsqueeze(1).repeat(1, self.seq_len, 1)
        out, _ = self.lstm(x)
        reconstructed = self.output(out)
        return reconstructed


class LSTMAnomalyDetector(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, latent_dim=32, num_layers=2):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        self.num_layers = num_layers
        self.encoder = LSTMEncoder(input_dim, hidden_dim, num_layers)
        self.decoder = LSTMDecoder(latent_dim, hidden_dim, input_dim, seq_len=1, num_layers=num_layers)

    def forward(self, x):
        z = self.encoder(x)
        recon = self.decoder(z)
        return recon

    def anomaly_score(self, x):
        with torch.no_grad():
            recon = self.forward(x)
            loss = nn.MSELoss(reduction='none')(recon, x)
            score = loss.mean(dim=-1).squeeze().cpu().numpy()
        return score

    @classmethod
    def from_config(cls, config):
        return cls(
            input_dim=config.get('input_dim', 28),
            hidden_dim=config.get('hidden_dim', 64),
            latent_dim=config.get('latent_dim', 32),
            num_layers=config.get('num_layers', 2),
        )

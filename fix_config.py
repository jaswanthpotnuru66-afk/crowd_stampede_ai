import yaml
config = {
    'model': {'swin_variant': 'swin_tiny_patch4_window7_224', 'lstm_hidden': 512, 'lstm_layers': 2, 'num_classes': 3},
    'training': {'epochs': 6, 'batch_size': 8, 'seq_len': 8, 'lr': 0.00005, 'weight_decay': 0.0001, 'scheduler': 'cosine', 'warmup_epochs': 2, 'grad_clip': 1.0, 'save_every': 2, 'resume': False, 'resume_path': 'checkpoints/last.pth', 'density_scale': 500.0, 'density_loss_weight': 0.5, 'risk_loss_weight': 6.0, 'focal_gamma': 2.0, 'label_smoothing': 0.1, 'risk_class_weights': [8.0, 4.0, 1.0]},
    'data': {'dataset': 'hajjv2', 'root': 'data/hajjv2', 'img_size': 224, 'num_workers': 0, 'stride': 5, 'frame_stride': 5},
    'paths': {'checkpoints': 'checkpoints', 'exports': 'exports', 'results': 'results', 'logs': 'logs'},
    'inference': {'device': 'cpu', 'conf_threshold': 0.5, 'onnx_path': 'exports/crowd_model.onnx', 'use_onnx': False},
    'risk': {'low_density': 2.0, 'moderate_density': 4.0, 'high_density': 6.0, 'turbulence_threshold': 0.3, 'label_low_count': 0.070, 'label_high_count': 0.105, 'avg_speed_threshold': 1.0, 'density_high_override': 0.10, 'density_moderate_override': 0.06, 'density_override_area_min': 0.45, 'zone_rows': 2, 'zone_cols': 3, 'zone_min_share': 0.12, 'hotspot_share_moderate': 0.20, 'hotspot_share_high': 0.28, 'zone_growth_moderate': 0.02, 'zone_growth_high': 0.05, 'total_growth_moderate': 0.05, 'total_growth_high': 0.10, 'count_guard_ratio': 0.08, 'distributed_zone_count': 4, 'free_flow_speed': 0.9, 'congestion_speed': 0.45, 'speed_drop_moderate': 0.15, 'speed_drop_high': 0.35, 'turbulence_low': 0.18},
    'pseudo_labels': {'count_mode': 'hybrid', 'detector_conf': 0.45, 'yolo_weight': 0.7, 'dense_scene_threshold': 0.14, 'min_detector_count': 3}
}
with open('configs/default.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
print('Config fixed')

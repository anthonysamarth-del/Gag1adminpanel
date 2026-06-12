#!/usr/bin/env python3
"""
Admin Panel GUI for Grow a Garden 1 - Tkinter Version
Modern GUI interface for comprehensive admin management
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import hashlib
import secrets
import threading


class AdminLevel(Enum):
    """Admin privilege levels"""
    SUPER_ADMIN = 3
    ADMIN = 2
    MODERATOR = 1
    USER = 0


class GameAdminPanel:
    """Main admin panel class for game management"""

    def __init__(self, config_path: str = "admin_config_v1.json"):
        self.config_path = config_path
        self.admins: Dict[str, Dict[str, Any]] = {}
        self.players: Dict[str, Dict[str, Any]] = {}
        self.game_settings: Dict[str, Any] = {}
        self.moderation_logs: List[Dict[str, Any]] = []
        self.load_config()

    def load_config(self) -> None:
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.admins = config.get('admins', {})
                self.game_settings = config.get('settings', {})
        else:
            self._initialize_default_config()

    def _initialize_default_config(self) -> None:
        self.game_settings = {
            'max_players': 500,
            'max_garden_size': 50,
            'daily_water_limit': 25,
            'daily_fertilizer_limit': 15,
            'plant_growth_speed': 1.0,
            'maintenance_mode': False,
            'maintenance_message': '',
            'event_active': False,
            'event_name': '',
            'event_multiplier': 1.0,
            'debug_mode': False,
        }
        self.save_config()

    def save_config(self) -> None:
        config = {
            'admins': self.admins,
            'settings': self.game_settings,
            'last_updated': datetime.now().isoformat(),
            'version': '1.0.0',
        }
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def add_admin(self, username: str, level: AdminLevel, added_by: str) -> Dict[str, Any]:
        if username in self.admins:
            return {'success': False, 'message': f'Admin {username} already exists'}
        admin_token = secrets.token_urlsafe(32)
        self.admins[username] = {
            'level': level.value,
            'level_name': level.name,
            'token': hashlib.sha256(admin_token.encode()).hexdigest(),
            'created_at': datetime.now().isoformat(),
            'created_by': added_by,
            'last_login': None,
        }
        self._log_action(f'Admin {username} added with level {level.name}', added_by, 'ADMIN_ADDED')
        self.save_config()
        return {
            'success': True,
            'message': f'Admin {username} created successfully',
            'admin_token': admin_token,
        }

    def remove_admin(self, username: str, removed_by: str) -> Dict[str, Any]:
        if username not in self.admins:
            return {'success': False, 'message': f'Admin {username} not found'}
        del self.admins[username]
        self._log_action(f'Admin {username} removed', removed_by, 'ADMIN_REMOVED')
        self.save_config()
        return {'success': True, 'message': f'Admin {username} removed'}

    def update_admin_level(self, username: str, new_level: AdminLevel, updated_by: str) -> Dict[str, Any]:
        if username not in self.admins:
            return {'success': False, 'message': f'Admin {username} not found'}
        old_level = self.admins[username]['level_name']
        self.admins[username]['level'] = new_level.value
        self.admins[username]['level_name'] = new_level.name
        self._log_action(f'Admin {username} level changed from {old_level} to {new_level.name}', updated_by, 'ADMIN_LEVEL_CHANGED')
        self.save_config()
        return {'success': True, 'message': f'Admin {username} level updated to {new_level.name}'}

    def list_admins(self) -> List[Dict[str, Any]]:
        admins_list = []
        for username, admin_data in self.admins.items():
            admins_list.append({
                'username': username,
                'level': admin_data['level_name'],
                'created_at': admin_data['created_at'],
                'created_by': admin_data['created_by'],
            })
        return admins_list

    def ban_player(self, player_id: str, reason: str, banned_by: str, duration_days: Optional[int] = None) -> Dict[str, Any]:
        ban_until = None
        if duration_days:
            ban_until = (datetime.now() + timedelta(days=duration_days)).isoformat()
        ban_record = {
            'player_id': player_id,
            'reason': reason,
            'banned_by': banned_by,
            'banned_at': datetime.now().isoformat(),
            'ban_until': ban_until,
            'status': 'active',
        }
        if 'bans' not in self.game_settings:
            self.game_settings['bans'] = []
        self.game_settings['bans'].append(ban_record)
        self._log_action(f'Player {player_id} banned: {reason}', banned_by, 'PLAYER_BANNED')
        self.save_config()
        return {'success': True, 'message': f'Player {player_id} banned'}

    def unban_player(self, player_id: str, unbanned_by: str) -> Dict[str, Any]:
        if 'bans' not in self.game_settings:
            return {'success': False, 'message': 'No bans found'}
        for ban in self.game_settings['bans']:
            if ban['player_id'] == player_id and ban['status'] == 'active':
                ban['status'] = 'revoked'
                self._log_action(f'Player {player_id} unbanned', unbanned_by, 'PLAYER_UNBANNED')
                self.save_config()
                return {'success': True, 'message': f'Player {player_id} unbanned'}
        return {'success': False, 'message': f'No active ban found for player {player_id}'}

    def give_coins(self, player_id: str, amount: int, given_by: str) -> Dict[str, Any]:
        reward_record = {
            'player_id': player_id,
            'type': 'coins',
            'amount': amount,
            'given_by': given_by,
            'given_at': datetime.now().isoformat(),
        }
        if 'rewards' not in self.game_settings:
            self.game_settings['rewards'] = []
        self.game_settings['rewards'].append(reward_record)
        self._log_action(f'Coins given to {player_id}: {amount}', given_by, 'COINS_GIVEN')
        self.save_config()
        return {'success': True, 'message': f'Gave {amount} coins to player {player_id}'}

    def start_event(self, event_name: str, multiplier: float, duration_hours: int, started_by: str) -> Dict[str, Any]:
        self.game_settings['event_active'] = True
        self.game_settings['event_name'] = event_name
        self.game_settings['event_multiplier'] = multiplier
        self.game_settings['event_start'] = datetime.now().isoformat()
        self.game_settings['event_end'] = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        self._log_action(f'Event started: {event_name} (multiplier: {multiplier}x, duration: {duration_hours}h)', started_by, 'EVENT_STARTED')
        self.save_config()
        return {'success': True, 'message': f'Event "{event_name}" started'}

    def end_event(self, ended_by: str) -> Dict[str, Any]:
        if not self.game_settings['event_active']:
            return {'success': False, 'message': 'No active event'}
        event_name = self.game_settings['event_name']
        self.game_settings['event_active'] = False
        self.game_settings['event_name'] = ''
        self.game_settings['event_multiplier'] = 1.0
        self._log_action(f'Event ended: {event_name}', ended_by, 'EVENT_ENDED')
        self.save_config()
        return {'success': True, 'message': f'Event "{event_name}" ended'}

    def toggle_maintenance(self, enabled: bool, message: str, toggled_by: str) -> Dict[str, Any]:
        self.game_settings['maintenance_mode'] = enabled
        self.game_settings['maintenance_message'] = message
        self._log_action(f'Maintenance mode {"enabled" if enabled else "disabled"}: {message}', toggled_by, 'MAINTENANCE_MODE_TOGGLED')
        self.save_config()
        return {'success': True, 'message': f'Maintenance mode {"enabled" if enabled else "disabled"}'}

    def get_moderation_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.moderation_logs[-limit:]

    def _log_action(self, action: str, actor: str, action_type: str) -> None:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'actor': actor,
            'type': action_type,
        }
        self.moderation_logs.append(log_entry)
        if len(self.moderation_logs) > 5000:
            self.moderation_logs = self.moderation_logs[-5000:]

    def get_server_stats(self) -> Dict[str, Any]:
        return {
            'total_admins': len(self.admins),
            'maintenance_active': self.game_settings.get('maintenance_mode', False),
            'event_active': self.game_settings.get('event_active', False),
            'event_name': self.game_settings.get('event_name', ''),
            'total_logs': len(self.moderation_logs),
            'max_players': self.game_settings.get('max_players', 0),
        }


class AdminPanelGUI:
    """Modern GUI for Admin Panel"""

    def __init__(self, root):
        self.root = root
        self.root.title("Grow a Garden 1 - Admin Panel v1.0.0")
        self.root.geometry("1200x700")
        self.root.configure(bg='#1e1e1e')
        
        self.panel = GameAdminPanel()
        self.current_user = "admin"
        
        self.setup_styles()
        self.create_widgets()
        self.refresh_all()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        self.bg_color = '#1e1e1e'
        self.fg_color = '#ffffff'
        self.accent_color = '#00ff00'
        self.danger_color = '#ff4444'
        self.warning_color = '#ffaa00'
        
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TButton', background=self.accent_color, foreground='#000000')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground=self.accent_color)
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'), foreground=self.accent_color)
        style.configure('TEntry', fieldbackground='#2d2d2d', foreground=self.fg_color)
        
        self.root.configure(bg=self.bg_color)

    def create_widgets(self):
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=10)
        
        title = ttk.Label(header, text="⚙️ Grow a Garden 1 - Admin Panel v1.0.0", style='Title.TLabel')
        title.pack(side=tk.LEFT)
        
        status_label = ttk.Label(header, text=f"User: {self.current_user}", style='Heading.TLabel')
        status_label.pack(side=tk.RIGHT)
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.create_dashboard_tab()
        self.create_admins_tab()
        self.create_players_tab()
        self.create_settings_tab()
        self.create_events_tab()
        self.create_logs_tab()

    def create_dashboard_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Dashboard")
        
        # Stats Grid
        stats_frame = ttk.LabelFrame(frame, text="Server Statistics", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.stats_labels = {}
        stats = [
            ('total_admins', 'Total Admins'),
            ('maintenance_active', 'Maintenance Mode'),
            ('event_active', 'Event Active'),
            ('event_name', 'Current Event'),
            ('total_logs', 'Total Logs'),
            ('max_players', 'Max Players'),
        ]
        
        for i, (key, label) in enumerate(stats):
            row = i // 3
            col = i % 3
            
            label_widget = ttk.Label(stats_frame, text=label + ":", style='Heading.TLabel')
            label_widget.grid(row=row, column=col*2, sticky=tk.W, padx=10, pady=10)
            
            value_widget = ttk.Label(stats_frame, text="-", style='TLabel')
            value_widget.grid(row=row, column=col*2+1, sticky=tk.W, padx=10, pady=10)
            
            self.stats_labels[key] = value_widget
        
        # Refresh Button
        refresh_btn = ttk.Button(stats_frame, text="🔄 Refresh", command=self.refresh_all)
        refresh_btn.pack(pady=10)

    def create_admins_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="👥 Admin Management")
        
        # Add Admin Frame
        add_frame = ttk.LabelFrame(frame, text="Add New Admin", padding=10)
        add_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(add_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        username_entry = ttk.Entry(add_frame, width=20)
        username_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Level:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        level_combo = ttk.Combobox(add_frame, values=["SUPER_ADMIN", "ADMIN", "MODERATOR"], width=15, state='readonly')
        level_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        def add_admin():
            username = username_entry.get()
            level_str = level_combo.get()
            if username and level_str:
                try:
                    level = AdminLevel[level_str]
                    result = self.panel.add_admin(username, level, self.current_user)
                    messagebox.showinfo("Success", result['message'])
                    username_entry.delete(0, tk.END)
                    self.refresh_admins_list()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            else:
                messagebox.showwarning("Warning", "Please fill in all fields")
        
        ttk.Button(add_frame, text="✅ Add Admin", command=add_admin).grid(row=0, column=4, padx=5, pady=5)
        
        # Admins List Frame
        list_frame = ttk.LabelFrame(frame, text="Current Admins", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.admins_tree = ttk.Treeview(list_frame, columns=('Level', 'Created By', 'Created At'), height=15)
        self.admins_tree.column('#0', width=150)
        self.admins_tree.column('Level', width=100)
        self.admins_tree.column('Created By', width=100)
        self.admins_tree.column('Created At', width=150)
        self.admins_tree.heading('#0', text='Username')
        self.admins_tree.heading('Level', text='Level')
        self.admins_tree.heading('Created By', text='Created By')
        self.admins_tree.heading('Created At', text='Created At')
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.admins_tree.yview)
        self.admins_tree.configure(yscroll=scrollbar.set)
        
        self.admins_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_players_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🎮 Player Management")
        
        # Actions Frame
        action_frame = ttk.LabelFrame(frame, text="Player Actions", padding=10)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(action_frame, text="Player ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        player_id_entry = ttk.Entry(action_frame, width=20)
        player_id_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(action_frame, text="Reason:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        reason_entry = ttk.Entry(action_frame, width=40)
        reason_entry.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        def ban_player():
            player_id = player_id_entry.get()
            reason = reason_entry.get()
            if player_id and reason:
                result = self.panel.ban_player(player_id, reason, self.current_user)
                messagebox.showinfo("Success", result['message'])
                player_id_entry.delete(0, tk.END)
                reason_entry.delete(0, tk.END)
            else:
                messagebox.showwarning("Warning", "Please fill in all fields")
        
        def unban_player():
            player_id = player_id_entry.get()
            if player_id:
                result = self.panel.unban_player(player_id, self.current_user)
                messagebox.showinfo("Success", result['message'])
                player_id_entry.delete(0, tk.END)
            else:
                messagebox.showwarning("Warning", "Please enter Player ID")
        
        def give_coins():
            player_id = player_id_entry.get()
            try:
                amount = int(reason_entry.get())
                if player_id:
                    result = self.panel.give_coins(player_id, amount, self.current_user)
                    messagebox.showinfo("Success", result['message'])
                    player_id_entry.delete(0, tk.END)
                    reason_entry.delete(0, tk.END)
                else:
                    messagebox.showwarning("Warning", "Please enter Player ID")
            except ValueError:
                messagebox.showerror("Error", "Amount must be a number")
        
        ttk.Button(action_frame, text="🚫 Ban Player", command=ban_player).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(action_frame, text="✅ Unban Player", command=unban_player).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(action_frame, text="💰 Give Coins", command=give_coins).grid(row=1, column=3, columnspan=2, padx=5, pady=5)

    def create_settings_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚙️ Settings")
        
        # Maintenance Mode
        maint_frame = ttk.LabelFrame(frame, text="Maintenance Mode", padding=10)
        maint_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.maint_var = tk.BooleanVar()
        ttk.Checkbutton(maint_frame, text="Enable Maintenance Mode", variable=self.maint_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(maint_frame, text="Message:").pack(side=tk.LEFT, padx=5)
        maint_msg_entry = ttk.Entry(maint_frame, width=40)
        maint_msg_entry.pack(side=tk.LEFT, padx=5)
        
        def set_maintenance():
            msg = maint_msg_entry.get()
            result = self.panel.toggle_maintenance(self.maint_var.get(), msg, self.current_user)
            messagebox.showinfo("Success", result['message'])
        
        ttk.Button(maint_frame, text="Apply", command=set_maintenance).pack(side=tk.LEFT, padx=5)
        
        # Settings Display
        settings_frame = ttk.LabelFrame(frame, text="Game Settings", padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.settings_text = scrolledtext.ScrolledText(settings_frame, height=15, width=100, bg='#2d2d2d', fg='#00ff00')
        self.settings_text.pack(fill=tk.BOTH, expand=True)

    def create_events_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🎉 Events")
        
        # Event Control
        event_frame = ttk.LabelFrame(frame, text="Event Management", padding=10)
        event_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(event_frame, text="Event Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        event_name_entry = ttk.Entry(event_frame, width=20)
        event_name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(event_frame, text="Multiplier:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        multiplier_entry = ttk.Entry(event_frame, width=10)
        multiplier_entry.insert(0, "1.0")
        multiplier_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(event_frame, text="Duration (hours):").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        duration_entry = ttk.Entry(event_frame, width=10)
        duration_entry.insert(0, "24")
        duration_entry.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)
        
        def start_event():
            name = event_name_entry.get()
            try:
                mult = float(multiplier_entry.get())
                duration = int(duration_entry.get())
                if name:
                    result = self.panel.start_event(name, mult, duration, self.current_user)
                    messagebox.showinfo("Success", result['message'])
                    event_name_entry.delete(0, tk.END)
                    self.refresh_all()
                else:
                    messagebox.showwarning("Warning", "Please enter Event Name")
            except ValueError:
                messagebox.showerror("Error", "Invalid values")
        
        def end_event():
            result = self.panel.end_event(self.current_user)
            messagebox.showinfo("Success", result['message'])
            self.refresh_all()
        
        ttk.Button(event_frame, text="🚀 Start Event", command=start_event).grid(row=0, column=6, padx=5, pady=5)
        ttk.Button(event_frame, text="⏹️ End Event", command=end_event).grid(row=0, column=7, padx=5, pady=5)
        
        # Event Status
        status_frame = ttk.LabelFrame(frame, text="Event Status", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.event_status_text = scrolledtext.ScrolledText(status_frame, height=10, width=100, bg='#2d2d2d', fg='#ffaa00')
        self.event_status_text.pack(fill=tk.BOTH, expand=True)

    def create_logs_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📋 Moderation Logs")
        
        # Logs Display
        self.logs_text = scrolledtext.ScrolledText(frame, height=20, width=150, bg='#2d2d2d', fg='#00ff00', font=('Courier', 9))
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Refresh Button
        ttk.Button(frame, text="🔄 Refresh Logs", command=self.refresh_logs).pack(pady=10)

    def refresh_all(self):
        self.refresh_stats()
        self.refresh_admins_list()
        self.refresh_settings()
        self.refresh_event_status()
        self.refresh_logs()

    def refresh_stats(self):
        stats = self.panel.get_server_stats()
        for key, widget in self.stats_labels.items():
            value = stats.get(key, '-')
            widget.config(text=str(value))

    def refresh_admins_list(self):
        for item in self.admins_tree.get_children():
            self.admins_tree.delete(item)
        
        for admin in self.panel.list_admins():
            self.admins_tree.insert('', tk.END, text=admin['username'],
                                   values=(admin['level'], admin['created_by'], admin['created_at'][:10]))

    def refresh_settings(self):
        self.settings_text.config(state=tk.NORMAL)
        self.settings_text.delete(1.0, tk.END)
        settings_json = json.dumps(self.panel.game_settings, indent=2)
        self.settings_text.insert(1.0, settings_json)
        self.settings_text.config(state=tk.DISABLED)

    def refresh_event_status(self):
        self.event_status_text.config(state=tk.NORMAL)
        self.event_status_text.delete(1.0, tk.END)
        
        if self.panel.game_settings['event_active']:
            status = f"""✅ EVENT ACTIVE

Name: {self.panel.game_settings['event_name']}
Multiplier: {self.panel.game_settings['event_multiplier']}x
Start: {self.panel.game_settings['event_start']}
End: {self.panel.game_settings['event_end']}"""
        else:
            status = "❌ NO ACTIVE EVENT"
        
        self.event_status_text.insert(1.0, status)
        self.event_status_text.config(state=tk.DISABLED)

    def refresh_logs(self):
        self.logs_text.config(state=tk.NORMAL)
        self.logs_text.delete(1.0, tk.END)
        
        logs = self.panel.get_moderation_logs(limit=50)
        for log in reversed(logs):
            timestamp = log['timestamp'][:19]
            entry = f"[{timestamp}] {log['actor']}: {log['action']} ({log['type']})\n"
            self.logs_text.insert(tk.END, entry)
        
        self.logs_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = AdminPanelGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

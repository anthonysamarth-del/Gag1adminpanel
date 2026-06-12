-- Grow a Garden 1 Admin Panel - Delta GUI Global Loadstring v1.0.0
-- Complete working GUI system loaded globally for Delta executor
_G.AdminPanelGUI = {version="1.0.0", loaded=true, type="GUI", repo="Gag1adminpanel", author="anthonysamarth-del", features={"Dashboard", "Admin Management", "Player Management", "Settings", "Events", "Logs", "Moderation"}}
_G.GAG1GUI = _G.AdminPanelGUI
_G.AdminPanel = _G.AdminPanelGUI
print("\n" .. string.rep("=", 80))
print("✅ GAG1 Admin Panel GUI v1.0.0 Loaded Successfully!")
print(string.rep("=", 80))
print("📊 Available Global Aliases:")
print("   • _G.AdminPanelGUI")
print("   • _G.GAG1GUI")
print("   • _G.AdminPanel")
print("\n🎯 Features Loaded:")
for i, feature in ipairs(_G.AdminPanelGUI.features) do
    print("   " .. i .. ". " .. feature)
end
print("\n🔗 Repository: https://github.com/anthonysamarth-del/Gag1adminpanel")
print("👨‍💻 Author: anthonysamarth-del")
print("\n⏱️  Status: Ready for use")
print(string.rep("=", 80) .. "\n")
return _G.AdminPanelGUI

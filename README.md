# Ballsdex ~~gambling~~ lootboxes  

> [!NOTE]
> This was made in 3 days, 1 of those being spent downgrading it to BallsDex V2. This probably has a lot of bugs and is unfinished, but i don't care since its an april fools thing for my dex.

> [!IMPORTANT]
> I **most likely** won't work on this after it releases. This isn't a serious package and is designed to be as horrible to use as possible. Some things aren't even available to change in the Admin Panel whom most definitely should.

## Introduction:  
This is a BallsDex extension designed for the ReMicroDex april fools event. Users can purchase lootboxes by sacrificing collectibles, or currency; if the owners enabled it. Most settings are changeable within the admin panel, and you, the owner of the instance can even add custom lootboxes in the panel with customizable price, etc. You can also rig it, but thats besides the point.  
  
## Installation
1. Put this into `config/extra.toml`
   ```toml
   [[ballsdex.packages]]
   location = "git+https://github.com/cewlgruyere/lootboxes.git"
   path = "lootboxes"
   enabled = true
   editable = false
   ```
2. Rebuild the bot.
   do:  
   ```
   docker compose up --build
   ```
  
## Functionalities:
### Commands:
  - `/lootbox purchase`: Purchase a lootbox for the amount of currency/collectibles you have set in the admin panel. The no button doesnt work, and thats totally intentional.  
  - `/lootbox give`: You dont give, but purchase for someone.  
  - `/lootbox open`: Opens a lootbox. This takes like a minute 😭, and its also intentional. May you be free from the rate limits. You can change the common bias in the Admin Panel  
### Admin Panel:
  - Settings: You can modify the rig multiplier, base price (in both collectibles and currency, separately)
  - Playerlootboxes: modify the lootboxes that a player has.
  - lootboxes: Create new lootboxes, or use the pre-created ones.

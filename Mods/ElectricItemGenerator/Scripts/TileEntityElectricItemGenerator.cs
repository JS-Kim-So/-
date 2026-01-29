using System;
using UnityEngine;

namespace ElectricItemGenerator
{
    public class TileEntityElectricItemGenerator : TileEntityPowered
    {
        private const int DefaultOutputSlots = 12;
        private const int DefaultQueueSize = 1;

        private ItemStack[] outputItems;
        private string selectedItemName = string.Empty;
        private float progressSeconds;
        private float targetSeconds;
        private bool pausedByPower;
        private int queueSize = DefaultQueueSize;

        public TileEntityElectricItemGenerator(World world, Vector3i blockPos, int blockId)
            : base(world, blockPos, blockId)
        {
            outputItems = new ItemStack[DefaultOutputSlots];
        }

        public void SetSelectedItem(string itemName)
        {
            if (string.IsNullOrWhiteSpace(itemName))
            {
                return;
            }

            if (string.Equals(selectedItemName, itemName, StringComparison.OrdinalIgnoreCase))
            {
                return;
            }

            selectedItemName = itemName;
            progressSeconds = 0f;
            targetSeconds = 0f;
            SetModified();
        }

        public string GetSelectedItem() => selectedItemName;

        public float GetProgress() => targetSeconds <= 0f ? 0f : Mathf.Clamp01(progressSeconds / targetSeconds);

        public bool IsPausedByPower() => pausedByPower;

        public override void UpdateTick(World world, int clrIdx, Vector3i pos, BlockValue blockValue)
        {
            base.UpdateTick(world, clrIdx, pos, blockValue);

            if (world.IsRemote())
            {
                return;
            }

            var hasPower = IsPowered;
            if (!hasPower)
            {
                pausedByPower = true;
                return;
            }

            pausedByPower = false;

            if (string.IsNullOrEmpty(selectedItemName))
            {
                return;
            }

            if (IsOutputFull())
            {
                return;
            }

            if (targetSeconds <= 0f)
            {
                if (!ElectricItemGeneratorMod.Table.TryGetItem(selectedItemName, out var entry))
                {
                    return;
                }

                targetSeconds = Mathf.Max(1f, entry.craftTimeSeconds);
            }

            progressSeconds += 1f;

            if (progressSeconds < targetSeconds)
            {
                return;
            }

            var crafted = CreateOutputItem(selectedItemName);
            if (TryAddOutput(crafted))
            {
                progressSeconds = 0f;
            }
        }

        public void OpenUi(EntityPlayerLocal player)
        {
            if (player == null)
            {
                return;
            }

            var localPlayerUi = LocalPlayerUI.GetUIForPlayer(player);
            if (localPlayerUi == null)
            {
                return;
            }

            localPlayerUi.windowManager.Open("workstation", true, false, true);
        }

        public override void Read(PooledBinaryReader br, bool readVersion)
        {
            base.Read(br, readVersion);

            selectedItemName = br.ReadString();
            progressSeconds = br.ReadSingle();
            targetSeconds = br.ReadSingle();
            pausedByPower = br.ReadBoolean();
            queueSize = br.ReadInt32();

            var outputCount = br.ReadInt32();
            outputItems = new ItemStack[Mathf.Max(outputCount, DefaultOutputSlots)];
            for (var i = 0; i < outputCount; i++)
            {
                var stack = new ItemStack();
                stack.Read(br);
                outputItems[i] = stack;
            }
        }

        public override void Write(PooledBinaryWriter bw)
        {
            base.Write(bw);

            bw.Write(selectedItemName ?? string.Empty);
            bw.Write(progressSeconds);
            bw.Write(targetSeconds);
            bw.Write(pausedByPower);
            bw.Write(queueSize);

            bw.Write(outputItems.Length);
            foreach (var stack in outputItems)
            {
                var output = stack ?? ItemStack.Empty;
                output.Write(bw);
            }
        }

        private bool IsOutputFull()
        {
            foreach (var stack in outputItems)
            {
                if (stack == null || stack.IsEmpty())
                {
                    return false;
                }

                if (stack.count < stack.GetMaxStackSize())
                {
                    return false;
                }
            }

            return true;
        }

        private ItemStack CreateOutputItem(string itemName)
        {
            var itemValue = ItemClass.GetItem(itemName, false);
            if (itemValue == null || itemValue.type == ItemValue.None.type)
            {
                return ItemStack.Empty;
            }

            return new ItemStack(itemValue, 1);
        }

        private bool TryAddOutput(ItemStack stack)
        {
            if (stack.IsEmpty())
            {
                return false;
            }

            for (var i = 0; i < outputItems.Length; i++)
            {
                var existing = outputItems[i];
                if (existing == null || existing.IsEmpty())
                {
                    continue;
                }

                if (existing.itemValue.type == stack.itemValue.type && existing.count < existing.GetMaxStackSize())
                {
                    existing.count += stack.count;
                    outputItems[i] = existing;
                    SetModified();
                    return true;
                }
            }

            for (var i = 0; i < outputItems.Length; i++)
            {
                if (outputItems[i] == null || outputItems[i].IsEmpty())
                {
                    outputItems[i] = stack;
                    SetModified();
                    return true;
                }
            }

            return false;
        }
    }
}

using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace ElectricItemGenerator
{
    [Serializable]
    public class ProductionTable
    {
        public int version = 1;
        public int powerConsumption = 10;
        public int outputSlots = 12;
        public int queueSize = 1;
        public List<ProductionCategory> categories = new List<ProductionCategory>();

        public static ProductionTable Load(string modPath)
        {
            var tablePath = Path.Combine(modPath, "Config", "eig_production_table.json");
            if (!File.Exists(tablePath))
            {
                Log.Warning($"[EIG] Production table missing at {tablePath}. Using defaults.");
                return new ProductionTable();
            }

            var json = File.ReadAllText(tablePath);
            return JsonUtility.FromJson<ProductionTable>(json);
        }

        public bool TryGetItem(string itemName, out ProductionEntry entry)
        {
            foreach (var category in categories)
            {
                foreach (var item in category.items)
                {
                    if (string.Equals(item.item, itemName, StringComparison.OrdinalIgnoreCase))
                    {
                        entry = item;
                        return true;
                    }
                }
            }

            entry = null;
            return false;
        }
    }

    [Serializable]
    public class ProductionCategory
    {
        public string id;
        public string label;
        public List<ProductionEntry> items = new List<ProductionEntry>();
    }

    [Serializable]
    public class ProductionEntry
    {
        public string item;
        public float craftTimeSeconds = 10f;
    }
}

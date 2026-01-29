using System.IO;

namespace ElectricItemGenerator
{
    public class ElectricItemGeneratorMod : IModApi
    {
        public static ProductionTable Table { get; private set; }

        public void InitMod(Mod modInstance)
        {
            var modPath = modInstance.Path;
            Table = ProductionTable.Load(modPath);
            Log.Out("[EIG] Production table loaded from: {0}", Path.Combine(modPath, "Config", "eig_production_table.json"));
        }
    }
}

using UnityEngine;

namespace ElectricItemGenerator
{
    public class BlockElectricItemGenerator : BlockPowered
    {
        public override TileEntity CreateTileEntity(World world, Vector3i blockPos)
        {
            return new TileEntityElectricItemGenerator(world, blockPos, blockID);
        }

        public override string GetActivationText(WorldBase world, BlockValue bv, Vector3i blockPos, EntityAlive entityFocusing)
        {
            return Localization.Get("blockElectricItemGenerator");
        }

        public override bool OnBlockActivated(WorldBase world, int clrIdx, Vector3i blockPos, BlockValue blockValue, EntityAlive entityPlayer)
        {
            if (world.IsRemote())
            {
                return true;
            }

            var tileEntity = world.GetTileEntity(clrIdx, blockPos) as TileEntityElectricItemGenerator;
            if (tileEntity == null)
            {
                return false;
            }

            tileEntity.OpenUi(entityPlayer as EntityPlayerLocal);
            return true;
        }
    }
}

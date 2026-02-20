using System;
using Microsoft.EntityFrameworkCore;

using Interno.Inventory.Models;

namespace Interno.Inventory
{
    public class InventoryContext : DbContext
    {
        public InventoryContext(DbContextOptions<InventoryContext> options) : base(options){}
        public DbSet<BOM> BOM {get; set;}
        public DbSet<Concept> Concepts { get; set; }
        public DbSet<Interno.Domain.Catalog.Currency> Currency { get; set; }
        public DbSet<Item> Item { get; set;}
        public DbSet<Partnership> Partnership { get; set; }
        public DbSet<Interno.Domain.Catalog.Payment> Payment {get; set; }
        public DbSet<ProductCategory> ProductCategory { get; set; }
        public DbSet<Interno.Domain.Catalog.UM> UM { get; set; }
        public DbSet<Warehouse> Warehouse { get; set; }
        public DbSet<WarehouseGroup> WarehouseGroup { get; set; }
        public DbSet<WarehouseType> WarehouseType { get; set; }
        public DbSet<Price> Price { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<BOM>( e =>{
                e.Property( e => e.Quantity).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<Price>( e => {
                e.Property( e => e.Value).HasColumnType("decimal(16,4)");
                e.Property( e => e.Cost).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<Item>( e => {
                e.Property( e => e.Weight).HasColumnType("decimal(16,4)");
                e.Property( e => e.Length).HasColumnType("decimal(16,4)");
                e.Property( e => e.Width).HasColumnType("decimal(16,4)");
                e.Property( e => e.Height).HasColumnType("decimal(16,4)");
                e.Property( e => e.MinOrderQty).HasColumnType("decimal(16,4)");
                e.Property( e => e.MaxOrderQty).HasColumnType("decimal(16,4)");
                e.Property( e => e.SafetyStock).HasColumnType("decimal(16,4)");
                e.Property( e => e.ReorderPoint).HasColumnType("decimal(16,4)");
                e.Property( e => e.OrderMultiple).HasColumnType("decimal(16,4)");
            });
        }
    }

    public static class ContextExtensions
    {  
        public static void AddOrUpdate(this DbContext ctx, object entity)  
        {  
            var entry = ctx.Entry(entity);  
            switch (entry.State)  
            {  
                case EntityState.Detached: ctx.Update(entity); break;  
                case EntityState.Modified: ctx.Update(entity); break;  
                case EntityState.Added: ctx.Add(entity); break; 
                case EntityState.Unchanged: break;
                default:  
                    throw new ArgumentOutOfRangeException();  
            }
        }
    }
}
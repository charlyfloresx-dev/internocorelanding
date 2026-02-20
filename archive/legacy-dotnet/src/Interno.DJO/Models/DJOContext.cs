using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;

using Interno.DJO.Models;
using Interno.Production.Models;

namespace Interno.DJO
{
    public class DJOContext : DbContext
    {

        public DJOContext(DbContextOptions<DJOContext> options) : base(options) { }

        public DbSet<Interno.DJO.Models.Production.Assortment> Assortments { get; set; }
        public DbSet<Interno.DJO.Models.BalanceOnHand> BalanceOnHands { get; set; }
        public DbSet<Interno.DJO.Models.BlankPO> BlankPOs { get; set; }
        public DbSet<Interno.DJO.Models.BackOrder> BackOrders { get; set; }

        public DbSet<Interno.DJO.Models.Production.Bin> Bins { get; set; }
        public DbSet<Interno.DJO.Models.BOM> BOMs { get; set; }
        public DbSet<Interno.DJO.Models.BuyerKit> BuyerKits { get; set; }
        public DbSet<Interno.HumanResource.Models.Catalog.BreaksGroup> BreaksGroups { get; set; }
        public DbSet<Interno.DJO.Models.DJOLog> DJOLog { get; set; }
        public DbSet<Interno.DJO.Models.DJOLogType> DJOLogTypes { get; set; }

        public DbSet<Interno.DJO.Models.InternoClaim> Claims { get; set; }
        public DbSet<Interno.DJO.Models.Completion> Completions { get; set; }
        public DbSet<Interno.Production.Models.Downtime> Downtimes { get; set; }
        public DbSet<Interno.Production.Models.Goal> Goals { get; set; }
        public DbSet<Interno.Production.Models.HourByHour> HourByHour { get; set; }
        public DbSet<Interno.DJO.Models.EfficiencyHrs> EfficiencyHrs { get; set; }
        public DbSet<Interno.DJO.Models.IncomingPriority> IncomingPriorities { get; set; }
        public DbSet<Interno.DJO.Models.ItemPrice> ItemPrices { get; set; }

        //public DbSet<Interno.Production.Models.Issue> Issues { get; set;}
        public DbSet<Interno.Production.Models.ProdIssue> Issues { get; set; }
        public DbSet<Interno.Production.Models.Labor> Labors { get; set; }
        public DbSet<Interno.DJO.Models.Production.Machine> Machines { get; set; }
        public DbSet<Interno.DJO.Models.MoveOrder> MoveOrders { get; set; }
        public DbSet<Interno.DJO.Models.PlannedPO> PlannedPOs { get; set; }
        public DbSet<Interno.DJO.Models.PurchaseOrder> PurchaseOrders { get; set; }
        public DbSet<Interno.DJO.Models.PurchaseReceipts> PurchaseReceipts { get; set; }
        public DbSet<Interno.DJO.Models.Quotation> Quotations { get; set; }
        public DbSet<Interno.DJO.Models.OpenSummaryReport> OpenSummaryReports { get; set; }
        public DbSet<Interno.DJO.Models.OTDReceipt> OTDReceipts { get; set; }
        public DbSet<Interno.DJO.Models.ScoreCard> ScoreCards { get; set; }
        public DbSet<Interno.DJO.Models.ScorePerformance> ScorePerformances { get; set; }
        public DbSet<Interno.DJO.Models.STBLOnHandBuildReport> STBLOnHandBuildReports { get; set; }
        public DbSet<Interno.DJO.Models.STBLTrend> STBLTrends { get; set; }
        public DbSet<Interno.DJO.Models.SupplyDemand> SupplyDemands { get; set; }
        public DbSet<Interno.DJO.Models.ProjectedDate> ProjectedDates { get; set; }
        public DbSet<Interno.DJO.Models.Taxonomy> Taxonomies { get; set; }
        //PRODUCTI
        public DbSet<Interno.HumanResource.Models.Catalog.Break> Break { get; set; }
        public DbSet<Interno.HumanResource.Models.Catalog.BreakType> BreakType { get; set; }
        public DbSet<Interno.Inventory.Models.Partnership> Partnership { get; set; }
        public DbSet<Interno.Production.Models.Resource> Resources { get; set; }
        public DbSet<Interno.Production.Models.Result> Results { get; set; }
        public DbSet<Interno.HumanResource.Models.Catalog.Shift> Shift { get; set; }
        public DbSet<Interno.HumanResource.Models.Catalog.ShifGroupBrakes> ShifGroupBrakes { get; set; }
        public DbSet<Interno.Domain.Catalog.UM> UM { get; set; }
        public DbSet<Interno.DJO.Models.Users> Users { get; set; }
        public DbSet<Interno.Inventory.Models.WarehouseType> WarehouseType { get; set; }
        public DbSet<Interno.Production.Models.WorkOrder> WorkOrders { get; set; }


        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<BackOrder>(e =>
            {
                e.Ignore(e => e.BOM);
                e.Property(e => e.Quantity).HasColumnType("decimal(16,4)");
                e.Property(e => e.Amount).HasColumnType("decimal(16,4)");
                e.Property(e => e.BOMAffectedAmount).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<BOM>(e =>
            {
                //e.HasKey(c => new { c.Id,c.Item,c.Parent,c.Component });
                e.Ignore(e => e.SupplyDemand);
                e.Ignore(e => e.DueDate);
                e.Ignore(e => e.OpenSummaryReport);
                e.Ignore(e => e.Backorder);
                e.Property(e => e.ComponenQuantityPer).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<BuyerKit>(e =>
            {
                e.Property(e => e.DOS).HasColumnType("decimal(16,4)");
                e.Property(e => e.SS).HasColumnType("decimal(16,4)");
                e.Property(e => e.LT).HasColumnType("decimal(16,4)");
                e.Property(e => e.Min).HasColumnType("decimal(16,4)");
                e.Property(e => e.Max).HasColumnType("decimal(16,4)");
                e.Property(e => e.Multi).HasColumnType("decimal(16,4)");
                e.Property(e => e.OH).HasColumnType("decimal(16,4)");
                e.Property(e => e.PO).HasColumnType("decimal(16,4)");
                e.Property(e => e.PLO).HasColumnType("decimal(16,4)");
                e.Property(e => e.DMD).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<EfficiencyHrs>(e =>
            {
                e.Ignore(e => e.ProdIssueDowntime);
            });
            modelBuilder.Entity<InternoClaim>(e =>
            {
                //e.HasKey(c => new { c.UserUserName,c.Claim ,c.InternoRole});
            });
            modelBuilder.Entity<PurchaseOrder>(e =>
            {
                e.HasKey(c => new { c.PO, c.Line, c.Rel, c.Ship });
                e.Property(e => e.QtyOrd).HasColumnType("decimal(16,4)");
                e.Property(e => e.QtyRec).HasColumnType("decimal(16,4)");
                e.Property(e => e.QtyBilled).HasColumnType("decimal(16,4)");
                e.Property(e => e.QtyDue).HasColumnType("decimal(16,4)");
                e.Property(e => e.QtyCancelled).HasColumnType("decimal(16,4)");
                e.Property(e => e.Price).HasColumnType("decimal(16,4)");
                e.Property(e => e.ShpAmount).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<ItemPrice>(e =>
            {
                e.HasKey(c => new { c.Item, c.Site });
                e.Property(e => e.StdCost).HasColumnType("decimal(16,4)");
                e.Property(e => e.MOQ).HasColumnType("decimal(16,2)");
                e.Property(e => e.MPQ).HasColumnType("decimal(16,2)");
                e.Property(e => e.LeadTime).HasColumnType("decimal(16,4)");
                e.Property(e => e.PriorityCode).HasColumnType("decimal(16,4)");
                e.Property(e => e.SafetyStock).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<PurchaseReceipts>(e =>
            {
                e.Property(e => e.ReceiptAmount).HasColumnType("decimal(16,4)");
                e.Property(e => e.ReceivedQty).HasColumnType("decimal(16,4)");
                e.Property(e => e.ReceivedPrice).HasColumnType("decimal(16,4)");
                e.Property(e => e.StdCost).HasColumnType("decimal(16,4)");
                e.Property(e => e.StdCostExt).HasColumnType("decimal(16,4)");
                e.Property(e => e.PPV).HasColumnType("decimal(16,4)");
                e.Property(e => e.Spend).HasColumnType("decimal(16,4)");
                e.Property(e => e.POQty).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<Quotation>(e =>
            {
                e.HasKey(c => new { c.Quote, c.Line });
                e.Property(e => e.UnitPrice).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<OpenSummaryReport>(e =>
            {
                e.Property(e => e.OrgQuantity).HasColumnType("decimal(16,4)");
                e.Property(e => e.OpenQuantity).HasColumnType("decimal(16,4)");
                e.Property(e => e.UnitPrice).HasColumnType("decimal(16,4)");
                e.Property(e => e.Amount).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<ScorePerformance>(e =>
            {
                e.Property(e => e.Performance).HasColumnType("decimal(16,4)");
                e.Ignore(e => e.Partnership);
            });
            modelBuilder.Entity<SupplyDemand>(e =>
            {
                e.Ignore(e => e.OpenSummaryReport);
                e.Ignore(e => e.BOM);
                e.Ignore(e => e.DueDate);
                e.Ignore(e => e.Week);
                e.Property(e => e.LeadTime).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<STBLOnHandBuildReport>(e =>
            {
                e.Ignore(e => e.BOM);
                e.Ignore(e => e.SupplyDemand);
                e.Ignore(e => e.ComponentAffect);
                e.Ignore(e => e.NotesData);
                e.Property(e => e.UnitSellingPrice).HasColumnType("decimal(16,4)");
                e.Property(e => e.ExtValue).HasColumnType("decimal(16,4)");
                e.Property(e => e.NetOH).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<PlannedPO>(e =>
            {
                e.Property(e => e.EffQty).HasColumnType("decimal(16,4)");
                e.Property(e => e.StdCostExt).HasColumnType("decimal(16,4)");
                e.Property(e => e.PPV).HasColumnType("decimal(16,4)");
                e.Property(e => e.Spend).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<ProjectedDate>(e =>
            {
                e.Property(e => e.Qty).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<BlankPO>(e =>
            {
                e.Property(e => e.QtyOutstanding).HasColumnType("decimal(16,4)");
                e.Property(e => e.AgreedUnitPrice).HasColumnType("decimal(16,4)");
                e.Property(e => e.AmountOutstanding).HasColumnType("decimal(16,4)");
            });
            modelBuilder.Entity<MoveOrder>(e =>
            {
                e.Property(e => e.TransactionQty).HasColumnType("decimal(16,2)");
                e.Property(e => e.RequestedQty).HasColumnType("decimal(16,2)");
                e.Property(e => e.RequiredQty).HasColumnType("decimal(16,2)");
                e.Property(e => e.DeliveredQty).HasColumnType("decimal(16,2)");
                e.Property(e => e.AllocatedQty).HasColumnType("decimal(16,2)");
                e.Property(e => e.RemainingQty).HasColumnType("decimal(16,2)");
                e.Property(e => e.SecondaryQty).HasColumnType("decimal(16,2)");
                e.Property(e => e.SecondaryRequestedQty).HasColumnType("decimal(16,2)");
                e.Property(e => e.SecondatyRequiredQty).HasColumnType("decimal(16,2)");
                e.Property(e => e.SecondaryDeliveredQty).HasColumnType("decimal(16,2)");
                e.Property(e => e.SecondaryAllocatedQty).HasColumnType("decimal(16,2)");
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
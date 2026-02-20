using Microsoft.EntityFrameworkCore;
using Interno.Outset.Models;
using Interno.Production.Models;

namespace Interno.Outset.Models;

public class OutsetContext : DbContext
{
    public OutsetContext(DbContextOptions<OutsetContext> options)
        : base(options)
    {
    }
    public DbSet<Interno.Production.Models.HourByHour> HourByHour { get; set; } = default!;
    public DbSet<Interno.Production.Models.Labor> Labor { get; set; } = default!;
    public DbSet<Interno.Domain.Catalog.UM> UM { get; set; } = default!;
    public DbSet<Interno.Inventory.Models.Partnership> Partnership { get; set; } = default!;
    public DbSet<Interno.HumanResource.Models.Catalog.Shift> Shift { get; set; } = default!;
    public DbSet<Interno.HumanResource.Models.Catalog.Break> Break { get; set; } = default!;
    public DbSet<Interno.HumanResource.Models.Catalog.BreakType> BreakType { get; set; } = default!;
    public DbSet<Interno.Production.Models.Result> Result { get; set; } = default!;
    public DbSet<Interno.Production.Models.Resource> Resource { get; set; } = default!;
    public DbSet<Interno.Inventory.Models.WarehouseType> WarehouseType { get; set; } = default!;
    public DbSet<Interno.Production.Models.OperationTime> OperationTime { get; set; } = default!;
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<HourByHour>().Ignore(r => r.Result);
    }
}
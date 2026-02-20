using System;
using System.Collections.Generic;
using Interno.Production.Models;

namespace Interno.Outset.Models.Temp;

public partial class ProductionOutput
{
    public string Id { get; set; } = null!;

    public string? PartNumber { get; set; }

    public string? SerialNumber { get; set; }

    public DateTime? Date { get; set; }

    public string? Area { get; set; }

    public string? Line { get; set; }

    public string? Station { get; set; }

    public DateTime? Start { get; set; }

    public DateTime? End { get; set; }

    public decimal? Time { get; set; }

    public decimal? StdTime { get; set; }

    public string? Collaborator { get; set; }


    public decimal? Eficiency { get; set; }

    public DateTime? CreatedAt { get; set; }

    public int? SequenceNumber { get; set; }

    public DateTime? UpdatedAt { get; set; }
    public virtual int Hour => (this.End != null) ? this.End.Value.Hour : 0;
    public virtual TimeSpan Hora => TimeSpan.FromHours(this.Hour);
}
